# Testing the Updated Pipeline

## What Changed

The pipeline now runs **TWO steps automatically** when you click "Load Data":

1. **Step 1 (0-50%)**: Load CSV from disk
2. **Step 2 (50-100%)**: Derive target variables

The Data Inspector now receives **processed data** with derived columns instead of raw CSV data.

## How to Test

### 1. Run the Application

```bash
cd biomarkers_app
python main.py
```

### 2. Load Data

1. Go to **Pipeline Flow** tab (first tab)
2. Click **"Load Data"** button
3. Watch the progress bar:
   - Should progress from 0% → 50% (Loading CSV)
   - Then 50% → 100% (Deriving targets)
4. Check the debug console (bottom panel):
   - Should show messages for both steps

### 3. Check Results

In the Pipeline Flow tab, you should see:
```
[SUCCESS] Pipeline completed successfully!

Steps: Load Data → Derive Targets

Rows: 252
Columns: 66 (was 47 in raw CSV)
...
```

**Key change:** Column count should be **66** (not 47)
- 47 original columns from CSV
- 19 derived columns (5 gates + 14 response targets)

### 4. Check Data Inspector

1. Switch to **Data Inspector** tab (second tab)
2. Status should say: "Processed Data: 252 rows × 66 columns"
3. Look for derived columns in the table:
   - `D30_evaluable_gate`
   - `D90_evaluable_gate`
   - `M6_evaluable_gate`
   - `Y1_evaluable_gate`
   - `BEST_evaluable_gate`
   - `D30_response_3class`
   - `D90_is_cr`
   - `cart_response_6_mos`
   - `cart_response_1_yr`
   - `best_response`
   - And more...

### 5. Check Column Info Tab

1. In Data Inspector, go to **Column Info** tab
2. Select column dropdown - should show 66 columns
3. Select `D30_response_3class` - should show:
   - Data type: object/category
   - Unique values: 3 (CR, PR, NR/PD)
   - Value counts for each response type

### 6. Check Statistics Tab

1. In Data Inspector, go to **Statistics** tab
2. Should show numeric stats for all numeric columns
3. Derived binary targets (like `D90_is_cr`) should appear as numeric (0/1)

## Expected Output

### Pipeline Flow Tab - Results:
```
[SUCCESS] Pipeline completed successfully!

Steps: Load Data → Derive Targets

Rows: 252
Columns: 66
Completeness: 87.3%
Missing values: 2,143
Load time: 0.5 seconds
```

### Data Inspector Tab - Status:
```
Processed Data: 252 rows × 66 columns
```

### Debug Console:
```
[INFO] 17:50:00 - [PipelineRunner] Starting data load operation
[INFO] 17:50:00 - [DataLoader] Checking file...
[INFO] 17:50:00 - [DataLoader] Reading CSV...
[INFO] 17:50:01 - [DataLoader] Validating...
[INFO] 17:50:01 - [DataLoader] Loaded 252 rows
[INFO] 17:50:01 - [TargetDerivation] Deriving targets...
[INFO] 17:50:01 - [TargetDerivation] Creating D30 evaluable gate
[INFO] 17:50:01 - [TargetDerivation] Creating response targets
[INFO] 17:50:02 - [TargetDerivation] Derived 19 target columns
[INFO] 17:50:02 - [DataInspector] Processed data loaded: 252 rows, 66 columns
```

## Troubleshooting

### If you see 47 columns instead of 66:
- The target derivation step failed silently
- Check debug console for errors
- Check that `unified_clinical_data.csv` has the required columns

### If progress bar doesn't show two phases:
- Check that the worker is using the updated code
- Try restarting the application

### If Data Inspector shows "No data loaded":
- The signal `data_loaded` may not be connecting
- Check debug console for exceptions

## Success Criteria ✅

- [ ] Progress bar shows 0% → 50% → 100%
- [ ] Debug console shows both "Load Data" and "Derive Targets" steps
- [ ] Results show "66 columns" (not 47)
- [ ] Data Inspector status shows "Processed Data: 252 rows × 66 columns"
- [ ] Data Inspector table includes derived columns (D30_evaluable_gate, etc.)
- [ ] All 48 tests still passing

## Next Steps

After confirming this works:
1. Mark test-integration task as complete
2. Begin Phase 3.2: Model Comparison Tab implementation
3. Start designing ModelComparisonWidget

---

**Last Updated:** January 18, 2026, 17:50
