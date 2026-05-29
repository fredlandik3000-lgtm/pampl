#!/usr/bin/env python3
"""
Generate visual mockup images for the Biomarkers Pipeline Tool documentation.
Creates professional-looking UI mockups as PNG files.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set style
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'Helvetica']

def create_mode_selection():
    """Create the mode selection startup dialog mockup."""
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Main window background
    window = FancyBboxPatch((5, 5), 90, 90, boxstyle="round,pad=0.5",
                            facecolor='#F5F5F5', edgecolor='#CCCCCC', linewidth=2)
    ax.add_patch(window)
    
    # Title bar
    title_bar = Rectangle((5, 90), 90, 5, facecolor='#0078D4', edgecolor='#0078D4')
    ax.add_patch(title_bar)
    ax.text(50, 92.5, '🧬 Biomarkers CAR-T Prediction Tool', ha='center', va='center',
            fontsize=14, fontweight='bold', color='white')
    
    # Main title
    ax.text(50, 83, 'Select Mode:', ha='center', va='top',
            fontsize=16, fontweight='bold', color='#333333')
    
    # Clinical Mode Box
    clinical_box = FancyBboxPatch((10, 55), 80, 22, boxstyle="round,pad=0.8",
                                  facecolor='#E8F5E9', edgecolor='#4CAF50', linewidth=3)
    ax.add_patch(clinical_box)
    ax.text(50, 73, '🏥 CLINICAL PREDICTION MODE', ha='center', va='top',
            fontsize=13, fontweight='bold', color='#2E7D32')
    ax.text(50, 68, 'Enter patient data and receive outcome predictions',
            ha='center', va='top', fontsize=10, color='#555555')
    ax.text(50, 65, '→ For clinicians making treatment decisions',
            ha='center', va='top', fontsize=9, color='#666666', style='italic')
    
    # Launch button
    btn = FancyBboxPatch((35, 57), 30, 5, boxstyle="round,pad=0.3",
                         facecolor='#4CAF50', edgecolor='#2E7D32', linewidth=2)
    ax.add_patch(btn)
    ax.text(50, 59.5, 'Launch Clinical Mode', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    # Research Mode Box
    research_box = FancyBboxPatch((10, 30), 80, 22, boxstyle="round,pad=0.8",
                                  facecolor='#E3F2FD', edgecolor='#2196F3', linewidth=3)
    ax.add_patch(research_box)
    ax.text(50, 48, '🔬 RESEARCH & DEVELOPMENT MODE', ha='center', va='top',
            fontsize=13, fontweight='bold', color='#0D47A1')
    ax.text(50, 43, 'Full pipeline access for model training & analysis',
            ha='center', va='top', fontsize=10, color='#555555')
    ax.text(50, 40, '→ For researchers and data scientists',
            ha='center', va='top', fontsize=9, color='#666666', style='italic')
    
    # Launch button
    btn2 = FancyBboxPatch((35, 32), 30, 5, boxstyle="round,pad=0.3",
                          facecolor='#2196F3', edgecolor='#0D47A1', linewidth=2)
    ax.add_patch(btn2)
    ax.text(50, 34.5, 'Launch Research Mode', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    # Demo Mode Box
    demo_box = FancyBboxPatch((10, 5), 80, 22, boxstyle="round,pad=0.8",
                              facecolor='#FFF3E0', edgecolor='#FF9800', linewidth=3)
    ax.add_patch(demo_box)
    ax.text(50, 23, '📊 DEMO MODE', ha='center', va='top',
            fontsize=13, fontweight='bold', color='#E65100')
    ax.text(50, 18, 'View pre-computed results and visualizations',
            ha='center', va='top', fontsize=10, color='#555555')
    ax.text(50, 15, '→ For presentations and demonstrations',
            ha='center', va='top', fontsize=9, color='#666666', style='italic')
    
    # Launch button
    btn3 = FancyBboxPatch((35, 7), 30, 5, boxstyle="round,pad=0.3",
                          facecolor='#FF9800', edgecolor='#E65100', linewidth=2)
    ax.add_patch(btn3)
    ax.text(50, 9.5, 'Launch Demo Mode', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    # Warning banner
    warning_box = Rectangle((10, -2), 80, 5, facecolor='#FFF9E6', edgecolor='#FFC107')
    ax.add_patch(warning_box)
    ax.text(50, 1.5, '⚠ RESEARCH USE ONLY - NOT FOR CLINICAL DIAGNOSIS ⚠',
            ha='center', va='top', fontsize=9, fontweight='bold', color='#F57C00')
    ax.text(50, 0, 'Predictions are for research purposes. Always consult complete clinical information.',
            ha='center', va='center', fontsize=7, color='#666666')
    
    plt.tight_layout()
    output_path = os.path.join(SCRIPT_DIR, 'mockup_1_mode_selection.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("[OK] Created " + os.path.basename(output_path))


def create_clinical_input():
    """Create the clinical prediction input form mockup."""
    fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
    ax.set_xlim(0, 140)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Main window
    window = Rectangle((0, 0), 140, 100, facecolor='#FAFAFA', edgecolor='#CCCCCC', linewidth=2)
    ax.add_patch(window)
    
    # Title bar
    title_bar = Rectangle((0, 95), 140, 5, facecolor='#4CAF50', edgecolor='#4CAF50')
    ax.add_patch(title_bar)
    ax.text(5, 97.5, '🏥 Clinical Prediction Mode', ha='left', va='center',
            fontsize=12, fontweight='bold', color='white')
    ax.text(135, 97.5, '[Mode: Clinical] [−] [×]', ha='right', va='center',
            fontsize=9, color='white')
    
    # Menu bar
    menu_bar = Rectangle((0, 92), 140, 3, facecolor='#F5F5F5', edgecolor='#DDDDDD')
    ax.add_patch(menu_bar)
    ax.text(2, 93.5, 'File  Patient  Predict  Export  Help', ha='left', va='center',
            fontsize=9, color='#333333')
    
    # Warning banner
    warning = Rectangle((0, 89), 140, 3, facecolor='#FFF9E6', edgecolor='#FFC107')
    ax.add_patch(warning)
    ax.text(70, 90.5, '⚠ RESEARCH USE ONLY - Predictions are for research purposes. Not FDA approved.',
            ha='center', va='center', fontsize=8, fontweight='bold', color='#F57C00')
    
    # Left sidebar
    sidebar = Rectangle((0, 0), 18, 89, facecolor='#EEEEEE', edgecolor='#DDDDDD')
    ax.add_patch(sidebar)
    
    # Sidebar items
    sidebar_items = [
        ('📋 Patient\n   Input', 78),
        ('Demographics', 72),
        ('Disease', 68),
        ('Labs', 64),
        ('Phase Data', 60),
        ('🎯 Predict', 52),
        ('📊 Results', 44),
        ('📄 Report', 36),
    ]
    
    for item, y in sidebar_items:
        if '📋' in item or '🎯' in item or '📊' in item or '📄' in item:
            ax.text(2, y, item, ha='left', va='center', fontsize=9, fontweight='bold', color='#333333')
        else:
            ax.text(4, y, item, ha='left', va='center', fontsize=8, color='#666666')
    
    # Buttons
    buttons = [('New Patient', 18), ('Save', 13), ('Load...', 8), ('Clear', 3)]
    for btn_text, y in buttons:
        btn = FancyBboxPatch((2, y), 14, 3.5, boxstyle="round,pad=0.2",
                             facecolor='#2196F3', edgecolor='#1976D2', linewidth=1)
        ax.add_patch(btn)
        ax.text(9, y + 1.75, btn_text, ha='center', va='center',
                fontsize=8, fontweight='bold', color='white')
    
    # Main content area
    content_start_y = 85
    
    # Patient Information Section
    section1 = FancyBboxPatch((20, content_start_y - 8), 115, 8, boxstyle="round,pad=0.5",
                              facecolor='white', edgecolor='#DDDDDD', linewidth=1)
    ax.add_patch(section1)
    ax.text(22, content_start_y - 1, 'Patient Information', ha='left', va='top',
            fontsize=10, fontweight='bold', color='#333333')
    ax.text(22, content_start_y - 3, 'Patient ID:', ha='left', va='top', fontsize=8, color='#666666')
    input_box = Rectangle((38, content_start_y - 4.2), 15, 2.5, facecolor='white', edgecolor='#AAAAAA')
    ax.add_patch(input_box)
    ax.text(56, content_start_y - 3, '(optional, anonymized)', ha='left', va='top',
            fontsize=7, color='#999999', style='italic')
    ax.text(22, content_start_y - 6, 'Date: 2026-01-18', ha='left', va='top', fontsize=8, color='#666666')
    
    content_start_y -= 10
    
    # Demographics Section
    section2 = FancyBboxPatch((20, content_start_y - 12), 115, 12, boxstyle="round,pad=0.5",
                              facecolor='white', edgecolor='#DDDDDD', linewidth=1)
    ax.add_patch(section2)
    ax.text(22, content_start_y - 1, 'Demographics', ha='left', va='top',
            fontsize=10, fontweight='bold', color='#333333')
    
    # Form fields
    fields = [
        ('Age:', '[____] years', content_start_y - 3.5),
        ('Sex:', '[● Male  ○ Female]', content_start_y - 5.5),
        ('Weight:', '[____] kg', content_start_y - 7.5),
        ('Height:', '[____] cm  →  BSA: 1.85 m² (auto)', content_start_y - 9.5),
    ]
    
    for label, value, y in fields:
        ax.text(22, y, label, ha='left', va='center', fontsize=8, color='#666666')
        ax.text(38, y, value, ha='left', va='center', fontsize=8, color='#333333')
    
    content_start_y -= 14
    
    # Disease Characteristics Section
    section3 = FancyBboxPatch((20, content_start_y - 18), 115, 18, boxstyle="round,pad=0.5",
                              facecolor='white', edgecolor='#DDDDDD', linewidth=1)
    ax.add_patch(section3)
    ax.text(22, content_start_y - 1, 'Disease Characteristics', ha='left', va='top',
            fontsize=10, fontweight='bold', color='#333333')
    
    disease_fields = [
        ('Diagnosis:', '[DLBCL ▼]', content_start_y - 3.5),
        ('Stage:', '[III ▼]', content_start_y - 5.5),
        ('Prior Lines:', '[2 ▼]', content_start_y - 7.5),
        ('Refractory:', '[☑] Yes  [☐] No', content_start_y - 9.5),
        ('Bulky Disease:', '[☐] Yes  [☑] No', content_start_y - 11.5),
        ('CNS Involvement:', '[☐] Yes  [☑] No', content_start_y - 13.5),
        ('BM Involvement:', '[15] %', content_start_y - 15.5),
    ]
    
    for label, value, y in disease_fields:
        ax.text(22, y, label, ha='left', va='center', fontsize=8, color='#666666')
        ax.text(42, y, value, ha='left', va='center', fontsize=8, color='#333333')
    
    content_start_y -= 20
    
    # Laboratory Values Section
    section4 = FancyBboxPatch((20, content_start_y - 22), 115, 22, boxstyle="round,pad=0.5",
                              facecolor='white', edgecolor='#DDDDDD', linewidth=1)
    ax.add_patch(section4)
    ax.text(22, content_start_y - 1, 'Laboratory Values (Phase: [Day -6 ▼])', ha='left', va='top',
            fontsize=10, fontweight='bold', color='#333333')
    
    lab_fields = [
        ('WBC:', '[8.5] × 10⁹/L', '[✓ Normal]', '#4CAF50', content_start_y - 3.5),
        ('ANC:', '[4.2] × 10⁹/L', '[✓ Normal]', '#4CAF50', content_start_y - 5.5),
        ('Hemoglobin:', '[12.3] g/dL', '[✓ Normal]', '#4CAF50', content_start_y - 7.5),
        ('Platelets:', '[180] × 10⁹/L', '[✓ Normal]', '#4CAF50', content_start_y - 9.5),
        ('Creatinine:', '[0.9] mg/dL', '[✓ Normal]', '#4CAF50', content_start_y - 11.5),
        ('LDH:', '[245] U/L', '[⚠ Elevated]', '#FF9800', content_start_y - 13.5),
        ('Ferritin:', '[420] ng/mL', '[⚠ Elevated]', '#FF9800', content_start_y - 15.5),
        ('CRP:', '[8.5] mg/L', '[⚠ Elevated]', '#FF9800', content_start_y - 17.5),
        ('Albumin:', '[3.8] g/dL', '[✓ Normal]', '#4CAF50', content_start_y - 19.5),
    ]
    
    for label, value, status, color, y in lab_fields:
        ax.text(22, y, label, ha='left', va='center', fontsize=8, color='#666666')
        ax.text(42, y, value, ha='left', va='center', fontsize=8, color='#333333')
        ax.text(75, y, status, ha='left', va='center', fontsize=7, fontweight='bold', color=color)
    
    # Validation status
    check_box = Rectangle((20, 2), 115, 3, facecolor='#E8F5E9', edgecolor='#4CAF50')
    ax.add_patch(check_box)
    ax.text(70, 3.5, '✓ All required fields complete', ha='center', va='center',
            fontsize=9, fontweight='bold', color='#2E7D32')
    
    # Generate button
    gen_btn = FancyBboxPatch((50, 6), 40, 5, boxstyle="round,pad=0.5",
                             facecolor='#4CAF50', edgecolor='#2E7D32', linewidth=2)
    ax.add_patch(gen_btn)
    ax.text(70, 8.5, 'Generate Predictions', ha='center', va='center',
            fontsize=12, fontweight='bold', color='white')
    
    # Status bar
    status_bar = Rectangle((0, -3), 140, 3, facecolor='#F5F5F5', edgecolor='#DDDDDD')
    ax.add_patch(status_bar)
    ax.text(2, -1.5, 'Status: Ready for prediction | Models loaded: NN, LR, XGB, RF, CB',
            ha='left', va='center', fontsize=8, color='#333333')
    
    plt.tight_layout()
    output_path = os.path.join(SCRIPT_DIR, 'mockup_2_clinical_input.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("[OK] Created " + os.path.basename(output_path))


def create_prediction_results():
    """Create the prediction results view mockup."""
    fig, ax = plt.subplots(figsize=(14, 12), facecolor='white')
    ax.set_xlim(0, 140)
    ax.set_ylim(0, 120)
    ax.axis('off')
    
    # Main window
    window = Rectangle((0, 0), 140, 120, facecolor='#FAFAFA', edgecolor='#CCCCCC', linewidth=2)
    ax.add_patch(window)
    
    # Title bar
    title_bar = Rectangle((0, 115), 140, 5, facecolor='#4CAF50', edgecolor='#4CAF50')
    ax.add_patch(title_bar)
    ax.text(5, 117.5, '🏥 Prediction Results - Patient ID: 12345', ha='left', va='center',
            fontsize=12, fontweight='bold', color='white')
    ax.text(135, 117.5, '[Print] [Export] [×]', ha='right', va='center',
            fontsize=9, color='white')
    
    content_y = 110
    
    # Day 30 Response Section
    section1 = FancyBboxPatch((5, content_y - 38), 130, 38, boxstyle="round,pad=0.8",
                              facecolor='white', edgecolor='#4CAF50', linewidth=2)
    ax.add_patch(section1)
    ax.text(70, content_y - 2, 'Day 30 Response Prediction', ha='center', va='top',
            fontsize=12, fontweight='bold', color='#333333')
    
    # Complete Response
    ax.text(10, content_y - 7, '🟢 Complete Response (CR)', ha='left', va='top',
            fontsize=10, fontweight='bold', color='#2E7D32')
    ax.text(12, content_y - 9, 'Probability: 68%  [95% CI: 52-81%]', ha='left', va='top',
            fontsize=9, color='#666666')
    
    # Progress bar for CR
    bar_bg = Rectangle((12, content_y - 12), 115, 2, facecolor='#EEEEEE', edgecolor='#CCCCCC')
    ax.add_patch(bar_bg)
    bar_fill = Rectangle((12, content_y - 12), 78, 2, facecolor='#4CAF50', edgecolor='#2E7D32')
    ax.add_patch(bar_fill)
    
    ax.text(12, content_y - 14, '✓ LIKELY - This patient has a high probability of CR', ha='left', va='top',
            fontsize=8, fontweight='bold', color='#2E7D32')
    
    # Partial Response
    ax.text(10, content_y - 18, '🟡 Partial Response (PR)', ha='left', va='top',
            fontsize=10, fontweight='bold', color='#F57C00')
    ax.text(12, content_y - 20, 'Probability: 24%  [95% CI: 15-36%]', ha='left', va='top',
            fontsize=9, color='#666666')
    
    # Progress bar for PR
    bar_bg2 = Rectangle((12, content_y - 23), 115, 2, facecolor='#EEEEEE', edgecolor='#CCCCCC')
    ax.add_patch(bar_bg2)
    bar_fill2 = Rectangle((12, content_y - 23), 28, 2, facecolor='#FF9800', edgecolor='#F57C00')
    ax.add_patch(bar_fill2)
    
    # No Response
    ax.text(10, content_y - 27, '🔴 Minimal/No Response (NR)', ha='left', va='top',
            fontsize=10, fontweight='bold', color='#D32F2F')
    ax.text(12, content_y - 29, 'Probability: 8%   [95% CI: 3-18%]', ha='left', va='top',
            fontsize=9, color='#666666')
    
    # Progress bar for NR
    bar_bg3 = Rectangle((12, content_y - 32), 115, 2, facecolor='#EEEEEE', edgecolor='#CCCCCC')
    ax.add_patch(bar_bg3)
    bar_fill3 = Rectangle((12, content_y - 32), 9, 2, facecolor='#F44336', edgecolor='#D32F2F')
    ax.add_patch(bar_fill3)
    
    ax.text(12, content_y - 34, '✓ UNLIKELY', ha='left', va='top',
            fontsize=8, fontweight='bold', color='#D32F2F')
    
    # Summary line
    ax.text(70, content_y - 37, 'Overall Response Rate (CR + PR): 92% [95% CI: 82-97%]',
            ha='center', va='top', fontsize=9, fontweight='bold', color='#333333')
    
    content_y -= 40
    
    # Model Performance
    perf_box = Rectangle((5, content_y - 5), 130, 5, facecolor='#F5F5F5', edgecolor='#DDDDDD')
    ax.add_patch(perf_box)
    ax.text(70, content_y - 1.5, 'Model Performance (from validation):', ha='center', va='top',
            fontsize=9, fontweight='bold', color='#333333')
    ax.text(70, content_y - 3.5, 'Accuracy: 83% | Balanced Accuracy: 81% | AUC: 0.89',
            ha='center', va='top', fontsize=8, color='#666666')
    ax.text(70, content_y - 4.8, 'Validated on 252 patients with 5-fold cross-validation',
            ha='center', va='top', fontsize=7, color='#999999', style='italic')
    
    content_y -= 8
    
    # Toxicity Risk Section
    section2 = FancyBboxPatch((5, content_y - 12), 130, 12, boxstyle="round,pad=0.8",
                              facecolor='white', edgecolor='#FF9800', linewidth=2)
    ax.add_patch(section2)
    ax.text(70, content_y - 2, 'Toxicity Risk Assessment', ha='center', va='top',
            fontsize=12, fontweight='bold', color='#333333')
    
    tox_items = [
        ('⚠ CRS Grade ≥2:', '35% [95% CI: 21-52%]', 'MODERATE RISK', '#FF9800'),
        ('✓ ICANS Grade ≥2:', '18% [95% CI: 9-31%]', 'LOW RISK', '#4CAF50'),
        ('⚠ Infection (100 days):', '42% [95% CI: 28-58%]', 'MODERATE RISK', '#FF9800'),
    ]
    
    tox_y = content_y - 5
    for item, prob, risk, color in tox_items:
        ax.text(10, tox_y, item, ha='left', va='top', fontsize=9, fontweight='bold', color=color)
        ax.text(45, tox_y, prob, ha='left', va='top', fontsize=9, color='#666666')
        ax.text(90, tox_y, risk, ha='left', va='top', fontsize=9, fontweight='bold', color=color)
        tox_y -= 3
    
    content_y -= 14
    
    # Key Factors Section
    section3 = FancyBboxPatch((5, content_y - 20), 130, 20, boxstyle="round,pad=0.8",
                              facecolor='white', edgecolor='#2196F3', linewidth=2)
    ax.add_patch(section3)
    ax.text(70, content_y - 2, 'Key Factors Influencing Predictions', ha='center', va='top',
            fontsize=12, fontweight='bold', color='#333333')
    
    ax.text(10, content_y - 5, 'Top 5 contributing features:', ha='left', va='top',
            fontsize=9, fontweight='bold', color='#666666')
    
    factors = [
        '1. LDH level (elevated) → ↓ CR probability',
        '2. Prior lines of therapy (2) → ↓ CR probability',
        '3. Ferritin level → ↑ toxicity risk',
        '4. Age (52 years) → neutral',
        '5. BM involvement (15%) → ↓ CR probability',
    ]
    
    factor_y = content_y - 7
    for factor in factors:
        ax.text(15, factor_y, factor, ha='left', va='top', fontsize=8, color='#666666')
        factor_y -= 2.5
    
    # View details button
    detail_btn = FancyBboxPatch((40, content_y - 19), 60, 3, boxstyle="round,pad=0.3",
                                facecolor='#2196F3', edgecolor='#1976D2', linewidth=1)
    ax.add_patch(detail_btn)
    ax.text(70, content_y - 17.5, 'View Detailed Feature Analysis', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    
    content_y -= 22
    
    # Similar Patients Section
    section4 = FancyBboxPatch((5, content_y - 10), 130, 10, boxstyle="round,pad=0.8",
                              facecolor='#F5F5F5', edgecolor='#AAAAAA', linewidth=1)
    ax.add_patch(section4)
    ax.text(70, content_y - 2, 'Similar Patients (Training Data)', ha='center', va='top',
            fontsize=11, fontweight='bold', color='#333333')
    ax.text(10, content_y - 4.5, '8 similar patients found with comparable features:', ha='left', va='top',
            fontsize=8, color='#666666')
    ax.text(15, content_y - 6.5, '• 6/8 (75%) achieved Complete Response at Day 30', ha='left', va='top',
            fontsize=8, color='#666666')
    ax.text(15, content_y - 8, '• 2/8 (25%) experienced CRS Grade ≥2', ha='left', va='top',
            fontsize=8, color='#666666')
    ax.text(15, content_y - 9.5, '• Median follow-up: 18 months', ha='left', va='top',
            fontsize=8, color='#666666')
    
    content_y -= 12
    
    # Action buttons
    btn_y = content_y - 3
    btn1 = FancyBboxPatch((10, btn_y), 35, 4, boxstyle="round,pad=0.3",
                          facecolor='#2196F3', edgecolor='#1976D2', linewidth=1)
    ax.add_patch(btn1)
    ax.text(27.5, btn_y + 2, 'View Other Timepoints', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    
    btn2 = FancyBboxPatch((50, btn_y), 35, 4, boxstyle="round,pad=0.3",
                          facecolor='#4CAF50', edgecolor='#2E7D32', linewidth=1)
    ax.add_patch(btn2)
    ax.text(67.5, btn_y + 2, 'Generate PDF Report', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    
    btn3 = FancyBboxPatch((90, btn_y), 35, 4, boxstyle="round,pad=0.3",
                          facecolor='#9E9E9E', edgecolor='#616161', linewidth=1)
    ax.add_patch(btn3)
    ax.text(107.5, btn_y + 2, 'New Prediction', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    
    # Status bar
    status_bar = Rectangle((0, -3), 140, 3, facecolor='#F5F5F5', edgecolor='#DDDDDD')
    ax.add_patch(status_bar)
    ax.text(2, -1.5, 'Prediction completed in 2.3 seconds | Models: Ensemble of NN, XGB, RF',
            ha='left', va='center', fontsize=8, color='#333333')
    
    plt.tight_layout()
    output_path = os.path.join(SCRIPT_DIR, 'mockup_3_prediction_results.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("[OK] Created " + os.path.basename(output_path))


def create_research_mode():
    """Create the research mode main window mockup."""
    fig, ax = plt.subplots(figsize=(16, 10), facecolor='white')
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Main window
    window = Rectangle((0, 0), 160, 100, facecolor='#FAFAFA', edgecolor='#CCCCCC', linewidth=2)
    ax.add_patch(window)
    
    # Title bar
    title_bar = Rectangle((0, 95), 160, 5, facecolor='#2196F3', edgecolor='#2196F3')
    ax.add_patch(title_bar)
    ax.text(5, 97.5, '🔬 Research Mode - Biomarkers Pipeline Tool', ha='left', va='center',
            fontsize=12, fontweight='bold', color='white')
    ax.text(155, 97.5, '[Mode] [−] [□] [×]', ha='right', va='center',
            fontsize=9, color='white')
    
    # Menu bar
    menu_bar = Rectangle((0, 92), 160, 3, facecolor='#F5F5F5', edgecolor='#DDDDDD')
    ax.add_patch(menu_bar)
    ax.text(2, 93.5, 'File  Edit  View  Run  Tools  Help', ha='left', va='center',
            fontsize=9, color='#333333')
    
    # Left sidebar - Pipeline Steps
    sidebar = Rectangle((0, 0), 20, 92, facecolor='#EEEEEE', edgecolor='#DDDDDD')
    ax.add_patch(sidebar)
    
    ax.text(10, 87, 'Pipeline\nSteps', ha='center', va='top',
            fontsize=9, fontweight='bold', color='#333333')
    
    steps = [
        ('□ Load Data', 80, '#AAAAAA'),
        ('✓ Derive', 75, '#4CAF50'),
        ('✓ Features', 70, '#4CAF50'),
        ('⚙ Split', 65, '#2196F3'),
        ('□ Train', 60, '#AAAAAA'),
        ('□ Evaluate', 55, '#AAAAAA'),
        ('□ Registry', 50, '#AAAAAA'),
        ('□ Export', 45, '#AAAAAA'),
    ]
    
    for step, y, color in steps:
        ax.text(3, y, step, ha='left', va='center', fontsize=8, color=color, fontweight='bold')
    
    # Control buttons
    buttons = [
        ('Run All', 35, '#4CAF50'),
        ('Run Step', 30, '#2196F3'),
        ('Stop', 25, '#F44336'),
    ]
    
    for btn_text, y, color in buttons:
        btn = FancyBboxPatch((2, y), 16, 3.5, boxstyle="round,pad=0.2",
                             facecolor=color, edgecolor='#555555', linewidth=1)
        ax.add_patch(btn)
        ax.text(10, y + 1.75, btn_text, ha='center', va='center',
                fontsize=8, fontweight='bold', color='white')
    
    ax.text(10, 18, 'Parameters\n──────', ha='center', va='top',
            fontsize=8, fontweight='bold', color='#333333')
    
    param_btns = [
        ('Edit...', 13),
        ('Presets▼', 8),
    ]
    
    for btn_text, y in param_btns:
        btn = FancyBboxPatch((3, y), 14, 3, boxstyle="round,pad=0.2",
                             facecolor='#FFFFFF', edgecolor='#2196F3', linewidth=1)
        ax.add_patch(btn)
        ax.text(10, y + 1.5, btn_text, ha='center', va='center',
                fontsize=7, fontweight='bold', color='#2196F3')
    
    # Main content area - Pipeline Flow Diagram
    content = FancyBboxPatch((22, 30), 135, 60, boxstyle="round,pad=0.5",
                             facecolor='white', edgecolor='#DDDDDD', linewidth=1)
    ax.add_patch(content)
    
    ax.text(89.5, 88, 'Pipeline Flow', ha='center', va='top',
            fontsize=11, fontweight='bold', color='#333333')
    
    # Draw simple pipeline flow
    flow_y = 82
    
    # Step 1: Load Data (completed)
    step1 = FancyBboxPatch((30, flow_y), 20, 6, boxstyle="round,pad=0.3",
                           facecolor='#C8E6C9', edgecolor='#4CAF50', linewidth=2)
    ax.add_patch(step1)
    ax.text(40, flow_y + 3, '1. Load Data\n✓ Complete (0.5s)', ha='center', va='center',
            fontsize=7, fontweight='bold', color='#2E7D32')
    
    # Arrow
    ax.arrow(50, flow_y + 3, 8, 0, head_width=1, head_length=1, fc='#4CAF50', ec='#4CAF50')
    
    # Step 2: Derive Targets (completed)
    step2 = FancyBboxPatch((60, flow_y), 20, 6, boxstyle="round,pad=0.3",
                           facecolor='#C8E6C9', edgecolor='#4CAF50', linewidth=2)
    ax.add_patch(step2)
    ax.text(70, flow_y + 3, '2. Derive\nTargets\n✓ Complete (1.2s)', ha='center', va='center',
            fontsize=7, fontweight='bold', color='#2E7D32')
    
    # Arrow
    ax.arrow(80, flow_y + 3, 8, 0, head_width=1, head_length=1, fc='#4CAF50', ec='#4CAF50')
    
    # Step 3: Features (completed)
    step3 = FancyBboxPatch((90, flow_y), 20, 6, boxstyle="round,pad=0.3",
                           facecolor='#C8E6C9', edgecolor='#4CAF50', linewidth=2)
    ax.add_patch(step3)
    ax.text(100, flow_y + 3, '3. Prepare\nFeatures\n✓ Complete (3.8s)', ha='center', va='center',
            fontsize=7, fontweight='bold', color='#2E7D32')
    
    # Arrow
    ax.arrow(110, flow_y + 3, 8, 0, head_width=1, head_length=1, fc='#2196F3', ec='#2196F3')
    
    # Step 4: Split (running)
    step4 = FancyBboxPatch((120, flow_y), 20, 6, boxstyle="round,pad=0.3",
                           facecolor='#BBDEFB', edgecolor='#2196F3', linewidth=2)
    ax.add_patch(step4)
    ax.text(130, flow_y + 3, '4. Split Data\n⚙ Running... (60%)', ha='center', va='center',
            fontsize=7, fontweight='bold', color='#1976D2')
    
    # Progress bar for current step
    prog_bg = Rectangle((122, flow_y + 0.5), 16, 1, facecolor='#EEEEEE', edgecolor='#CCCCCC')
    ax.add_patch(prog_bg)
    prog_fill = Rectangle((122, flow_y + 0.5), 9.6, 1, facecolor='#2196F3', edgecolor='#1976D2')
    ax.add_patch(prog_fill)
    
    # Next steps (pending)
    flow_y = 72
    
    pending_steps = [
        ('5. Train Models\n(Est: 15 min)', 35),
        ('6. Evaluate\nModels', 65),
        ('7. Update\nRegistry', 95),
        ('8. Aggregate\nResults', 125),
    ]
    
    for step_text, x in pending_steps:
        step_box = FancyBboxPatch((x, flow_y), 20, 6, boxstyle="round,pad=0.3",
                                  facecolor='#F5F5F5', edgecolor='#AAAAAA', linewidth=1)
        ax.add_patch(step_box)
        ax.text(x + 10, flow_y + 3, step_text + '\n⚪ Pending', ha='center', va='center',
                fontsize=7, color='#666666')
    
    # Debug Console
    console = FancyBboxPatch((22, 5), 135, 22, boxstyle="round,pad=0.5",
                             facecolor='#263238', edgecolor='#37474F', linewidth=1)
    ax.add_patch(console)
    
    ax.text(24, 25, 'Debug Console', ha='left', va='top',
            fontsize=9, fontweight='bold', color='white')
    ax.text(145, 25, '[All▼] [Clear] [Export]', ha='right', va='top',
            fontsize=7, color='white')
    
    console_lines = [
        ('[INFO] 14:30:15 - Loading data from unified_clinical_data.csv', 22),
        ('[INFO] 14:30:16 - ✓ Loaded 252 rows, 47 columns', 20),
        ('[INFO] 14:30:16 - Deriving targets...', 18),
        ('[INFO] 14:30:17 - Created 5 gate columns', 16),
        ('[INFO] 14:30:18 - Created 14 derived target columns', 14),
        ('[INFO] 14:30:18 - ✓ Target derivation complete', 12),
        ('[INFO] 14:30:18 - Preparing features for phase_-6...', 10),
        ('[INFO] 14:30:20 - Created 124 features (phase_-6)', 8),
        ('[INFO] 14:30:20 - Preparing features for phase_0... ⚙', 6),
    ]
    
    for line, y in console_lines:
        if '✓' in line:
            ax.text(24, y, line, ha='left', va='top', fontsize=6, color='#4CAF50', family='monospace')
        elif '⚙' in line:
            ax.text(24, y, line, ha='left', va='top', fontsize=6, color='#2196F3', family='monospace')
        else:
            ax.text(24, y, line, ha='left', va='top', fontsize=6, color='#CCCCCC', family='monospace')
    
    # Status bar
    status_bar = Rectangle((0, -3), 160, 3, facecolor='#F5F5F5', edgecolor='#DDDDDD')
    ax.add_patch(status_bar)
    ax.text(2, -1.5, '⚙ Status: Running Step 4/8', ha='left', va='center',
            fontsize=8, fontweight='bold', color='#2196F3')
    ax.text(50, -1.5, 'Progress: 45%', ha='left', va='center', fontsize=8, color='#666666')
    ax.text(80, -1.5, 'Elapsed: 00:02:15', ha='left', va='center', fontsize=8, color='#666666')
    ax.text(110, -1.5, 'ETA: 00:03:00', ha='left', va='center', fontsize=8, color='#666666')
    
    plt.tight_layout()
    output_path = os.path.join(SCRIPT_DIR, 'mockup_4_research_mode.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("[OK] Created " + os.path.basename(output_path))


def main():
    """Generate all mockup images."""
    print("Generating UI mockup images...")
    print("-" * 50)
    
    create_mode_selection()
    create_clinical_input()
    create_prediction_results()
    create_research_mode()
    
    print("-" * 50)
    print("[OK] All mockup images generated successfully!")
    print("")
    print("Generated files:")
    print("  - mockup_1_mode_selection.png")
    print("  - mockup_2_clinical_input.png")
    print("  - mockup_3_prediction_results.png")
    print("  - mockup_4_research_mode.png")
    print("")
    print("You can now view these images in the docs/ folder.")


if __name__ == '__main__':
    main()
