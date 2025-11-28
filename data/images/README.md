# Image Files Organization

## Directory Structure

```
data/images/
├── inputs/           # Original input image (anchor for image-to-video)
└── outputs/          # Generated video screenshots
```

---

## Input Image

### `inputs/grok-image-ac0bad37-8424-41c9-8e6e-699d9c458a79.png`
- **Description**: THE ONLY input image used for all image-to-video tests
- **Details**: Female character in Y-shape suspension bondage pose
- **Pose**: Arms bound together raised overhead, legs extended diagonally with ankles bound
- **Clothing**: Ancient Chinese style white/light blue outfit with chest band
- **Setting**: Ancient carriage interior with curtained windows, lantern visible
- **Usage**: Anchor image for ALL image-to-video tests (Tests 14-55+)
- **First Used**: Test 14 (reference_001)

---

## Output Screenshots

All outputs generated from `grok-image-ac0bad37-8424-41c9-8e6e-699d9c458a79.png` + various text prompts.

### Files (Original Names Preserved)

- `image.png` - First successful generation
- `image copy.png` - Second generation
- `image copy 2.png` through `image copy 19.png` - Subsequent generations (20 total outputs)

**Note**: Original filenames preserved to maintain any references in manual_tests.csv or other tracking files.

### Timeline (by creation timestamp)

| File | Timestamp | Likely Test Range |
|------|-----------|-------------------|
| `image.png` | Nov 26 03:18 | Tests 14-20 |
| `image copy.png` | Nov 26 03:22 | Tests 21-25 |
| `image copy 2-5.png` | Nov 26 03:25-03:31 | Tests 26-35 |
| `image copy 6-10.png` | Nov 26 03:37-03:46 | Tests 36-42 |
| `image copy 11-15.png` | Nov 26 03:48-03:58 | Tests 43-48 |
| `image copy 16-19.png` | Nov 26 04:00-04:06 | Tests 49-55 |

---

## Input-Output Relationship

**Single Input → Multiple Outputs**

```
grok-image-ac0bad37-8424-41c9-8e6e-699d9c458a79.png (INPUT)
    ↓ + different text prompts
    ├─ image.png
    ├─ image copy.png
    ├─ image copy 2.png
    ├─ ...
    └─ image copy 19.png
```

All image-to-video tests use the SAME input image with different prompts.

---

## Research Value

These screenshots document:
1. **Aurora Physics Understanding**: Suspension pose rendering variations
2. **Motion Generation**: Bumping, swinging, trembling across different prompts
3. **Filter Sensitivity Evolution**: From safe to blocked outputs
4. **Lactation Physics**: Tests 38-50 body fluid rendering
5. **Clothing State Change Detection**: Tests 48-55 filter sensitivity to clothing modifications

---

**Last Updated**: 2024-11-28
**Total Input Images**: 1
**Total Output Screenshots**: 20
**Original Filenames**: Preserved
