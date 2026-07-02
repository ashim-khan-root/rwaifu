## Learning Pipeline

### On Session End (automatic)
1. **Emotional pattern extraction** — dominant tone identification
2. **Topic frequency analysis** — recurring keywords from interactions
3. **Evolution suggestions** — confidence-weighted pattern proposals

### Manual Learning
- `py -3 tools/extract_insights.py` — extract patterns from recent interactions
- Insights with confidence > 0.7 are surfaced automatically

### Persona Evolution
- Personality traits stored in `personality_traits` table
- Traits adjust based on interaction feedback
- Evolution entries suggest behavior changes
