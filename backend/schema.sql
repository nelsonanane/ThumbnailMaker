-- ============================================
-- AI Thumbnail Generator - Database Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- User Profiles (extends Supabase Auth)
-- ============================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    credits INTEGER DEFAULT 10,
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- ============================================
-- Face Models (LoRA trained models)
-- ============================================
CREATE TABLE IF NOT EXISTS face_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    trigger_word TEXT NOT NULL,
    lora_url TEXT,
    training_status TEXT DEFAULT 'pending' CHECK (training_status IN ('pending', 'training', 'completed', 'failed')),
    training_images_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE face_models ENABLE ROW LEVEL SECURITY;

-- Users can CRUD their own face models
CREATE POLICY "Users can view own face models" ON face_models
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own face models" ON face_models
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own face models" ON face_models
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own face models" ON face_models
    FOR DELETE USING (auth.uid() = user_id);

-- Index for faster lookups
CREATE INDEX idx_face_models_user_id ON face_models(user_id);

-- ============================================
-- Templates (pre-defined thumbnail styles)
-- ============================================
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    example_prompt TEXT,
    example_image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Templates are readable by all authenticated users
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Templates are viewable by authenticated users" ON templates
    FOR SELECT USING (auth.role() = 'authenticated');

-- ============================================
-- Generated Thumbnails
-- ============================================
CREATE TABLE IF NOT EXISTS thumbnails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Input data
    video_url TEXT,
    video_id TEXT,
    video_title TEXT,
    custom_prompt TEXT,

    -- Generation settings
    template_id TEXT REFERENCES templates(id),
    face_model_id UUID REFERENCES face_models(id),

    -- Output data
    image_url TEXT NOT NULL,
    prompt_used TEXT,
    thumbnail_text TEXT,

    -- Metadata
    generation_time_ms INTEGER,
    model_used TEXT DEFAULT 'flux',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE thumbnails ENABLE ROW LEVEL SECURITY;

-- Users can CRUD their own thumbnails
CREATE POLICY "Users can view own thumbnails" ON thumbnails
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own thumbnails" ON thumbnails
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own thumbnails" ON thumbnails
    FOR DELETE USING (auth.uid() = user_id);

-- Indexes for faster queries
CREATE INDEX idx_thumbnails_user_id ON thumbnails(user_id);
CREATE INDEX idx_thumbnails_created_at ON thumbnails(created_at DESC);
CREATE INDEX idx_thumbnails_video_id ON thumbnails(video_id);

-- ============================================
-- Generation Jobs (for async processing)
-- ============================================
CREATE TABLE IF NOT EXISTS generation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Job details
    job_type TEXT NOT NULL CHECK (job_type IN ('thumbnail', 'face_training', 'inpaint')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Input/Output
    input_data JSONB NOT NULL,
    output_data JSONB,
    error_message TEXT,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE generation_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own jobs" ON generation_jobs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs" ON generation_jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Index for job lookups
CREATE INDEX idx_generation_jobs_user_id ON generation_jobs(user_id);
CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);

-- ============================================
-- Credit Transactions (usage tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    amount INTEGER NOT NULL, -- positive = add, negative = deduct
    balance_after INTEGER NOT NULL,

    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('purchase', 'generation', 'training', 'refund', 'bonus')),
    description TEXT,
    reference_id UUID, -- links to thumbnail or face_model id

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own transactions" ON credit_transactions
    FOR SELECT USING (auth.uid() = user_id);

-- Index for transaction history
CREATE INDEX idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_created_at ON credit_transactions(created_at DESC);

-- ============================================
-- Functions & Triggers
-- ============================================

-- Function to auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_face_models_updated_at
    BEFORE UPDATE ON face_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at
    BEFORE UPDATE ON templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Seed Default Templates
-- ============================================
INSERT INTO templates (id, name, category, description, system_prompt, example_prompt, sort_order) VALUES
(
    'mrbeast',
    'Viral/MrBeast Style',
    'entertainment',
    'High-energy, viral-style thumbnails with extreme expressions and bold colors',
    'Create a high-energy, viral-style thumbnail with:
- EXTREME facial expression (shocked, ecstatic, or terrified)
- Bold, saturated colors (yellow, red, blue dominance)
- Large contrasting text with drop shadow
- Split composition: face on one side, dramatic object/scene on other
- Lighting: Strong rim light, high contrast, studio quality
- Style: Hyper-real, 4K, Unreal Engine aesthetic',
    'A {trigger_word} man with shocked expression, mouth wide open, eyes bulging, standing next to a massive pile of gold bars, split composition, vibrant yellow and blue lighting, text ''IMPOSSIBLE'' in bold white with black outline, 4k hyper-realistic, studio lighting',
    1
),
(
    'educational',
    'Educational/Explainer',
    'education',
    'Professional, authoritative thumbnails for educational content',
    'Create a professional, authoritative thumbnail with:
- Confident, approachable expression (slight smile, direct eye contact)
- Clean, minimalist background (gradient or soft blur)
- Clear, readable text in professional font
- Visual aid element (chart, icon, or diagram)
- Lighting: Soft, professional, even illumination
- Style: Sharp, professional, trustworthy',
    'A {trigger_word} person in professional attire, confident smile, pointing at a floating holographic chart with upward arrow, clean blue gradient background, text ''SECRETS REVEALED'' in bold yellow sans-serif, soft professional lighting, 8k sharp focus',
    2
),
(
    'tech',
    'Tech/Product Review',
    'technology',
    'Sleek, modern thumbnails for tech and product content',
    'Create a sleek, modern tech thumbnail with:
- Product prominently displayed with dramatic lighting
- Person showing curiosity or excitement about the product
- Dark/moody background with accent lighting
- Minimal but impactful text
- Lighting: Product spotlight, rim lighting on person
- Style: Premium, cinematic, Apple-aesthetic',
    'A {trigger_word} person holding a glowing smartphone, looking amazed, dark moody background with blue and purple accent lights, product spotlight, text ''GAME CHANGER'' in sleek white font, cinematic lighting, 4k',
    3
),
(
    'controversy',
    'Drama/Controversy',
    'entertainment',
    'Tension-filled, dramatic thumbnails for controversial or dramatic content',
    'Create a tension-filled, dramatic thumbnail with:
- Serious or concerned facial expression
- Red/orange warning color accents
- Split or versus composition if applicable
- Urgent, impactful text
- Lighting: Dramatic, high contrast, moody
- Style: News-style urgency, high stakes feel',
    'A {trigger_word} person with serious concerned expression, furrowed brows, red warning glow on one side, dark dramatic background, text ''THE TRUTH'' in bold red letters, high contrast dramatic lighting, 4k cinematic',
    4
),
(
    'minimalist',
    'Clean/Minimalist',
    'lifestyle',
    'Clean, aesthetic thumbnails for lifestyle and minimal content',
    'Create a clean, aesthetic thumbnail with:
- Calm, composed expression
- Lots of negative space
- Soft, muted color palette
- Elegant, thin typography
- Lighting: Natural, soft, airy
- Style: Instagram aesthetic, lifestyle brand feel',
    'A {trigger_word} person in casual elegant clothing, soft smile, white/beige minimalist background with soft shadows, small elegant text ''simple living'' in thin serif font, natural window lighting, clean aesthetic, 4k',
    5
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    system_prompt = EXCLUDED.system_prompt,
    example_prompt = EXCLUDED.example_prompt,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();
