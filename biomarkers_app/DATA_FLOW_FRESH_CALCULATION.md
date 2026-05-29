# Data Flow: Fresh Calculation Every Run

**Date:** January 18, 2026  
**Status:** Verified - No cached files, all fresh calculations  
**Concern:** Ensuring data inspector and all app components use fresh data

---

## Summary: Everything is Fresh ✓

**CONFIRMED:** The application recalculates everything from scratch on each run:
- ✓ CSV read fresh from disk
- ✓ Targets derived fresh (no cached derivations)
- ✓ Column info calculated fresh from in-memory DataFrame
- ✓ No reliance on old calculated files
- ✓ No pickle/json/cache files used

---

## Complete Data Flow

### Step 1: User Clicks "Load Data"

```
User Action → Load Button Click
```

### Step 2: CSV Loaded Fresh from Disk

**File:** `app/pipeline/wrappers/data_loader_wrapper.py`

```python
# Line 87
df = pd.read_csv(path)  # ← FRESH READ FROM CSV
```

**Properties:**
- Reads directly from CSV file
- No caching mechanism
- No intermediate saved files
- Fresh data on every load

### Step 3: Target Derivation (Fresh Calculation)

**File:** `app/pipeline/wrappers/target_derivation_wrapper.py`

```python
# Line 84: Make a copy (preserves original)
df_derived = df.copy()

# Line 94: Fresh calculation
df_derived = derive_targets_func(df_derived)
```

**What's Calculated Fresh:**
1. **Evaluability Gates** (5 gates)
   - `BEST_evaluable_gate`
   - `D30_evaluable_gate`
   - `D90_evaluable_gate`
   - `M6_evaluable_gate`
   - `Y1_evaluable_gate`

2. **Response Targets** (14 targets)
   - `D30_response_3class`
   - `D90_is_cr`
   - `crs_grade_ge2`
   - `icans_grade_ge2`
   - etc.

**Properties:**
- All calculated in-memory
- No cached target derivations
- No saved intermediate files
- Fresh calculation every time

### Step 4: In-Memory Data Transfer

**File:** `app/ui/widgets/pipeline_runner_widget.py`

```python
# Line 240: Emit processed DataFrame
self.data_loaded.emit(result.data)  # ← IN-MEMORY TRANSFER
```

**Properties:**
- DataFrame passed via Qt signal
- No file I/O at this stage
- Direct memory transfer
- No serialization/deserialization

### Step 5: Main Window Connection

**File:** `app/main_window.py`

```python
# Line 182: Connect signal to slot
self.pipeline_runner.data_loaded.connect(self.data_inspector.load_data)
```

**Properties:**
- Signal-slot connection (Qt mechanism)
- DataFrame passed by reference
- No copying or file operations

### Step 6: Data Inspector Receives DataFrame

**File:** `app/ui/widgets/data_inspector_widget.py`

```python
# Line 183-186: Receive and store DataFrame
def load_data(self, data: pd.DataFrame):
    self.data = data  # ← STORE IN MEMORY
    
    # Line 190: Identify derived columns (fresh analysis)
    self._identify_derived_columns()
    
    # Line 207: Calculate all views (fresh)
    self._refresh_all_views()
```

**Properties:**
- Receives fresh DataFrame
- No file loading
- All analysis done on this DataFrame

### Step 7: Column Info Calculation (On-Demand)

**All Calculated Fresh from `self.data`:**

```python
def _refresh_column_info(self):
    """Calculate column information fresh"""
    if self.data is None:
        return
    
    column_name = self.column_combo.currentText()
    if not column_name or column_name not in self.data.columns:
        return
    
    col_data = self.data[column_name]  # ← FROM IN-MEMORY DATAFRAME
    
    # Calculate fresh:
    info = f"Column: {column_name}\n"
    info += f"Data Type: {col_data.dtype}\n"
    info += f"Non-Null Count: {col_data.notna().sum():,}\n"
    info += f"Null Count: {col_data.isna().sum():,}\n"
    info += f"Unique Values: {col_data.nunique():,}\n"
    
    # Statistics calculated fresh
    if pd.api.types.is_numeric_dtype(col_data):
        info += f"Mean: {col_data.mean():.2f}\n"
        info += f"Std Dev: {col_data.std():.2f}\n"
        info += f"Min: {col_data.min():.2f}\n"
        info += f"Max: {col_data.max():.2f}\n"
```

**Properties:**
- All statistics calculated on-demand
- From in-memory DataFrame
- No cached statistics files
- Recalculated every time view is refreshed

---

## Verified: No Cached Files Used

### Search Results

**Searched for:**
- `cache`, `.pkl`, `.pickle`, `.hdf`, `.h5`, `to_json`, `read_json`

**Found:**
1. `main_window.py:357` - Menu item "Clear Cache" (NOT IMPLEMENTED)
2. `types.py:70` - Config option `cache_dir: str = "cache"` (NOT USED)

**Conclusion:** 
- Caching infrastructure planned but NOT implemented
- No cache files are read or written
- All data is fresh on every run

---

## No Intermediate File Saves

### Data Inspector: No Saves

**Searched for:**
- `to_csv`, `to_excel`, `to_parquet`, `save`

**Result:** NO MATCHES in `data_inspector_widget.py`

**Conclusion:**
- Data Inspector never saves data
- All operations read-only
- No file writes during inspection

---

## Data Freshness Guarantees

### 1. CSV Data is Fresh

**When:** Every time "Load Data" is clicked

**How:**
```python
df = pd.read_csv(path)  # Fresh read from disk
```

**Guarantees:**
- ✓ Latest file contents
- ✓ No stale data
- ✓ No cached CSV

### 2. Derived Targets are Fresh

**When:** Every time data is loaded

**How:**
```python
df_derived = derive_targets_func(df)  # Fresh calculation
```

**Guarantees:**
- ✓ Recalculated from raw data
- ✓ No cached derivations
- ✓ Latest logic applied

### 3. Column Info is Fresh

**When:** Every time a view is refreshed

**How:**
```python
self._refresh_all_views()  # Recalculate all statistics
```

**Guarantees:**
- ✓ Calculated from in-memory DataFrame
- ✓ No stale statistics
- ✓ Reflects current data

---

## What Happens on Each App Run

### First Time Running App

1. **App starts** → No data loaded
2. **User clicks "Load Data"** → Browse for CSV
3. **CSV loaded** → Read fresh from disk
4. **Targets derived** → Calculated fresh
5. **Data Inspector shows data** → Fresh statistics

### Second Time Running App (Same Session)

1. **User clicks "Load Data" again** → Browse for CSV
2. **Previous data discarded** → Memory cleared
3. **CSV loaded** → Read fresh from disk (even if same file!)
4. **Targets derived** → Calculated fresh again
5. **Data Inspector shows data** → Fresh statistics

### Next Day Running App

1. **App starts** → No data loaded (clean slate)
2. **User clicks "Load Data"** → Browse for CSV
3. **CSV loaded** → Read fresh from disk
4. **Targets derived** → Calculated fresh
5. **Data Inspector shows data** → Fresh statistics

**Key Point:** Every run is identical - always fresh!

---

## Memory Management

### How Data is Stored

```
PipelineRunner.worker.data (in PipelineWorker thread)
    ↓ (signal/slot transfer)
DataInspector.data (in main thread)
```

**Properties:**
- All data in RAM
- No persistent storage
- Garbage collected when app closes

### What Happens on App Close

```
App Close → All data freed from memory → Nothing saved to disk
```

**Next App Run:**
- Clean slate
- No residual data
- Must load fresh from CSV

---

## Future: If Caching Were Implemented (NOT CURRENT)

### Planned Caching Features (Not Yet Active)

1. **Pipeline Results Cache**
   - Save model training results
   - Avoid re-training same models
   - Would use `cache_dir` from config

2. **Feature Engineering Cache**
   - Save engineered features
   - Reuse for different models
   - Would speed up iteration

3. **Evaluation Results Cache**
   - Save ROC curves, confusion matrices
   - Avoid re-computing visualizations

**Current Status:** NONE OF THESE ARE IMPLEMENTED

---

## How to Force Fresh Data (Even Though It's Always Fresh)

### Method 1: Close and Reopen App
```
Close App → Reopen → Load Data
```
**Result:** 100% fresh (data freed from memory)

### Method 2: Click "Load Data" Again
```
Click "Load Data" button → Select CSV → Confirm
```
**Result:** Previous data discarded, fresh data loaded

### Method 3: Restart Pipeline
```
Cancel current pipeline → Start new pipeline run
```
**Result:** Fresh calculation from CSV

---

## Verification Test

### How to Verify Data is Fresh

1. **Modify CSV File**
   - Open `unified_clinical_data.csv`
   - Change a value (e.g., patient age)
   - Save CSV

2. **Reload in App**
   - Click "Load Data"
   - Select same CSV
   - Check Data Inspector

3. **Expected Result**
   - ✓ Modified value appears
   - ✓ Statistics updated
   - ✓ Derived targets reflect changes

### If You See Stale Data

**That would indicate a bug!** Please report:
- What changed in CSV?
- What shows in app?
- Steps to reproduce

---

## Comparison: Other Apps (What We DON'T Do)

### Bad Practice: Cached Everything

```python
# BAD EXAMPLE (we don't do this!)
if os.path.exists('cached_data.pkl'):
    df = pd.read_pickle('cached_data.pkl')  # Stale data!
else:
    df = pd.read_csv('data.csv')
    df.to_pickle('cached_data.pkl')
```

**Problems:**
- Stale data if CSV updated
- Hard to invalidate cache
- Users confused by old data

### Our Approach: Always Fresh

```python
# GOOD (our current approach)
df = pd.read_csv(path)  # Always fresh
df_derived = derive_targets(df)  # Always calculated
```

**Benefits:**
- ✓ Never stale data
- ✓ Consistent behavior
- ✓ No cache invalidation issues
- ✓ Users see latest data

---

## Configuration for Future Caching

### Current Config (Not Used)

```python
# app/pipeline/types.py
@dataclass
class PipelineConfig:
    enable_caching: bool = True  # ← Not used anywhere
    cache_dir: str = "cache"      # ← Not used anywhere
```

### If/When Caching is Implemented

**Would need:**
1. Cache key based on file hash + derivation logic
2. Cache invalidation on file modification
3. User option to force fresh calculation
4. Clear cache functionality

**Currently:** These fields exist but have NO EFFECT

---

## Summary

### Current Behavior (Verified)

✓ **CSV Data:** Read fresh from disk every time  
✓ **Derived Targets:** Calculated fresh every time  
✓ **Column Info:** Calculated fresh from in-memory DataFrame  
✓ **No Cached Files:** None read or written  
✓ **No Stale Data:** Impossible to get stale data  

### Data Flow Diagram

```
User Clicks "Load Data"
    ↓
Read CSV from disk (FRESH)
    ↓
Derive targets in-memory (FRESH CALCULATION)
    ↓
Pass DataFrame via Qt signal (IN-MEMORY)
    ↓
Data Inspector receives DataFrame
    ↓
Calculate column info on-demand (FRESH)
    ↓
Display to user (CURRENT DATA)
```

### Guarantees

1. **No stale data from previous runs**
2. **No reliance on cached files**
3. **All calculations fresh from raw CSV**
4. **Latest file contents always used**
5. **Statistics reflect current data**

---

**Answer to User's Concern:**

> "We can't rely on old calculated files"

**CORRECT - and we don't!** ✓

Everything is recalculated fresh on every run. There are no cached files that could become stale.

---

**Status:** Verified - All data is fresh on every run  
**Cache Files:** None (caching not implemented)  
**Data Source:** CSV read fresh + in-memory calculations  
**Stale Data Risk:** Zero - impossible with current architecture
