"""
Analysis and Visualization Script for AdaptiBreak Study Results
Generates graphs and statistical comparisons between Fixed and Adaptive conditions.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import config
from data_logger import AggregateAnalyzer


# Set plot style
sns.set_style("whitegrid")
sns.set_palette("Set2")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11


def load_all_data():
    """Load all session data into structured format."""
    sessions = AggregateAnalyzer.load_all_sessions()
    
    if not sessions:
        print("❌ No session data found!")
        print(f"   Please ensure study sessions are saved in: {config.LOG_DIRECTORY}")
        return None
    
    print(f"✓ Loaded {len(sessions)} sessions")
    
    # Convert to DataFrame
    data = []
    for session in sessions:
        if 'evaluation' not in session:
            continue
        
        row = {
            'participant_id': session['participant_id'],
            'mode': session['session_mode'],
            'test_score': session['evaluation'].get('test_score', None),
            'test_correct': session['evaluation'].get('test_correct', None),
            'test_total': session['evaluation'].get('test_total', None),
            'fatigue_rating': session['evaluation'].get('fatigue_rating', None),
            'concentration': session['evaluation'].get('concentration_rating', None),
            'alertness': session['evaluation'].get('alertness_rating', None),
            'sus_score': session['evaluation'].get('sus_score', None),
            'avg_fatigue_detected': session.get('avg_fatigue', None),
            'max_fatigue_detected': session.get('max_fatigue', None),
            'duration_min': session.get('total_duration', 0) / 60
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    print(f"\nData Summary:")
    print(f"  Fixed mode sessions: {len(df[df['mode'] == 'fixed'])}")
    print(f"  Adaptive mode sessions: {len(df[df['mode'] == 'adaptive'])}")
    print(f"  Unique participants: {df['participant_id'].nunique()}")
    
    return df


def plot_test_performance(df):
    """Compare test performance between conditions."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Box plot
    sns.boxplot(data=df, x='mode', y='test_score', ax=ax1)
    ax1.set_title('Test Score by Condition', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Study Mode', fontsize=12)
    ax1.set_ylabel('Test Score (%)', fontsize=12)
    ax1.set_xticklabels(['Fixed Timer', 'Adaptive'])
    
    # Add individual points
    sns.swarmplot(data=df, x='mode', y='test_score', ax=ax1, color='black', alpha=0.5, size=6)
    
    # Bar plot with error bars
    means = df.groupby('mode')['test_score'].mean()
    sems = df.groupby('mode')['test_score'].sem()
    
    modes = ['fixed', 'adaptive']
    x_pos = np.arange(len(modes))
    
    ax2.bar(x_pos, [means[mode] for mode in modes], 
            yerr=[sems[mode] for mode in modes],
            capsize=10, alpha=0.7)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(['Fixed Timer', 'Adaptive'])
    ax2.set_ylabel('Mean Test Score (%)', fontsize=12)
    ax2.set_title('Mean Test Performance', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 100)
    
    # Add value labels on bars
    for i, mode in enumerate(modes):
        ax2.text(i, means[mode] + sems[mode] + 2, f'{means[mode]:.1f}%', 
                ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('analysis_test_performance.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: analysis_test_performance.png")
    
    # Statistical test
    fixed_scores = df[df['mode'] == 'fixed']['test_score'].dropna()
    adaptive_scores = df[df['mode'] == 'adaptive']['test_score'].dropna()
    
    if len(fixed_scores) > 0 and len(adaptive_scores) > 0:
        t_stat, p_value = stats.ttest_rel(fixed_scores, adaptive_scores) if len(fixed_scores) == len(adaptive_scores) else stats.ttest_ind(fixed_scores, adaptive_scores)
        print(f"\n  t-test: t={t_stat:.3f}, p={p_value:.4f}")
        if p_value < 0.05:
            print(f"  ✓ Significant difference (p < 0.05)")
        else:
            print(f"  No significant difference (p >= 0.05)")


def plot_fatigue_ratings(df):
    """Compare subjective fatigue ratings."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    metrics = [
        ('fatigue_rating', 'Fatigue Rating', 'Higher = More Tired'),
        ('concentration', 'Concentration', 'Higher = Better'),
        ('alertness', 'Alertness', 'Higher = More Alert')
    ]
    
    for ax, (metric, title, label) in zip(axes, metrics):
        # Box plot
        sns.boxplot(data=df, x='mode', y=metric, ax=ax)
        sns.swarmplot(data=df, x='mode', y=metric, ax=ax, color='black', alpha=0.5, size=6)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Study Mode', fontsize=11)
        ax.set_ylabel(f'{title} (1-5 scale)', fontsize=11)
        ax.set_xticklabels(['Fixed Timer', 'Adaptive'])
        ax.set_ylim(0, 6)
        
        # Add mean values
        means = df.groupby('mode')[metric].mean()
        for i, mode in enumerate(['fixed', 'adaptive']):
            if mode in means.index:
                ax.text(i, 5.5, f'μ={means[mode]:.2f}', ha='center', fontweight='bold')
    
    plt.suptitle('Subjective Ratings Comparison', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('analysis_fatigue_ratings.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: analysis_fatigue_ratings.png")


def plot_sus_scores(df):
    """Compare System Usability Scale scores."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Box plot
    sns.boxplot(data=df, x='mode', y='sus_score', ax=ax1)
    sns.swarmplot(data=df, x='mode', y='sus_score', ax=ax1, color='black', alpha=0.5, size=6)
    
    ax1.set_title('SUS Score by Condition', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Study Mode', fontsize=12)
    ax1.set_ylabel('SUS Score (0-100)', fontsize=12)
    ax1.set_xticklabels(['Fixed Timer', 'Adaptive'])
    ax1.set_ylim(0, 100)
    
    # Add reference lines
    ax1.axhline(y=68, color='green', linestyle='--', alpha=0.5, label='Average (68)')
    ax1.axhline(y=80.3, color='blue', linestyle='--', alpha=0.5, label='Good (80.3)')
    ax1.legend()
    
    # Interpretation pie chart
    means = df.groupby('mode')['sus_score'].mean()
    
    colors_map = {'Excellent': '#2ecc71', 'Good': '#3498db', 'OK': '#f39c12', 'Poor': '#e74c3c'}
    
    def interpret_sus(score):
        if score >= 80.3:
            return 'Excellent'
        elif score >= 68:
            return 'Good'
        elif score >= 51:
            return 'OK'
        else:
            return 'Poor'
    
    interpretations = {mode: interpret_sus(means[mode]) for mode in means.index}
    
    ax2.text(0.5, 0.7, 'Mean SUS Scores', ha='center', fontsize=14, fontweight='bold', 
            transform=ax2.transAxes)
    
    y_pos = 0.5
    for mode in ['fixed', 'adaptive']:
        if mode in means.index:
            label = 'Fixed Timer' if mode == 'fixed' else 'Adaptive'
            interpretation = interpretations[mode]
            color = colors_map[interpretation]
            
            ax2.text(0.5, y_pos, f'{label}: {means[mode]:.1f} ({interpretation})',
                    ha='center', fontsize=12, transform=ax2.transAxes,
                    bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
            y_pos -= 0.15
    
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis('off')
    
    plt.tight_layout()
    plt.savefig('analysis_sus_scores.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: analysis_sus_scores.png")


def plot_biometric_fatigue(df):
    """Plot detected fatigue levels (adaptive mode only)."""
    adaptive_df = df[df['mode'] == 'adaptive'].dropna(subset=['avg_fatigue_detected'])
    
    if len(adaptive_df) == 0:
        print("⚠️  No biometric data available (adaptive mode only)")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Histogram of average fatigue
    ax1.hist(adaptive_df['avg_fatigue_detected'], bins=15, alpha=0.7, edgecolor='black')
    ax1.axvline(x=config.FATIGUE_SCORE_THRESHOLD, color='red', linestyle='--', 
               linewidth=2, label=f'Threshold ({config.FATIGUE_SCORE_THRESHOLD})')
    ax1.set_xlabel('Average Fatigue Score', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('Distribution of Detected Fatigue (Adaptive Mode)', fontsize=14, fontweight='bold')
    ax1.legend()
    
    # Correlation with subjective fatigue
    if 'fatigue_rating' in adaptive_df.columns:
        valid_data = adaptive_df.dropna(subset=['avg_fatigue_detected', 'fatigue_rating'])
        
        if len(valid_data) > 0:
            ax2.scatter(valid_data['avg_fatigue_detected'], valid_data['fatigue_rating'], 
                       s=100, alpha=0.6, edgecolors='black', linewidth=1)
            
            # Fit line
            z = np.polyfit(valid_data['avg_fatigue_detected'], valid_data['fatigue_rating'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(valid_data['avg_fatigue_detected'].min(), 
                                valid_data['avg_fatigue_detected'].max(), 100)
            ax2.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)
            
            # Calculate correlation
            corr, p_val = stats.pearsonr(valid_data['avg_fatigue_detected'], 
                                         valid_data['fatigue_rating'])
            
            ax2.set_xlabel('Detected Fatigue Score (Avg)', fontsize=12)
            ax2.set_ylabel('Subjective Fatigue Rating (1-5)', fontsize=12)
            ax2.set_title('Objective vs Subjective Fatigue', fontsize=14, fontweight='bold')
            ax2.text(0.05, 0.95, f'r = {corr:.3f}\np = {p_val:.4f}', 
                    transform=ax2.transAxes, fontsize=11,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                    verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig('analysis_biometric_fatigue.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: analysis_biometric_fatigue.png")


def plot_overall_comparison(df):
    """Create comprehensive comparison visualization."""
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    metrics = [
        ('test_score', 'Test Score (%)', 'higher_better'),
        ('fatigue_rating', 'Fatigue Rating', 'lower_better'),
        ('concentration', 'Concentration', 'higher_better'),
        ('alertness', 'Alertness', 'higher_better'),
        ('sus_score', 'SUS Score', 'higher_better'),
        ('avg_fatigue_detected', 'Detected Fatigue', 'lower_better')
    ]
    
    positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
    
    for (metric, label, direction), pos in zip(metrics, positions):
        ax = fig.add_subplot(gs[pos[0], pos[1]])
        
        data_to_plot = df.dropna(subset=[metric])
        if len(data_to_plot) == 0:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=12)
            ax.set_title(label, fontsize=11, fontweight='bold')
            ax.axis('off')
            continue
        
        # Bar plot with individual points
        means = data_to_plot.groupby('mode')[metric].mean()
        sems = data_to_plot.groupby('mode')[metric].sem()
        
        modes = [m for m in ['fixed', 'adaptive'] if m in means.index]
        x_pos = np.arange(len(modes))
        
        bars = ax.bar(x_pos, [means[mode] for mode in modes],
                     yerr=[sems[mode] for mode in modes],
                     capsize=8, alpha=0.7)
        
        # Color bars based on which is better
        if direction == 'higher_better' and len(modes) == 2:
            if means['adaptive'] > means['fixed']:
                bars[1].set_color('green')
                bars[1].set_alpha(0.8)
        elif direction == 'lower_better' and len(modes) == 2:
            if means['adaptive'] < means['fixed']:
                bars[1].set_color('green')
                bars[1].set_alpha(0.8)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(['Fixed' if m == 'fixed' else 'Adaptive' for m in modes], fontsize=9)
        ax.set_ylabel(label, fontsize=10)
        ax.set_title(label, fontsize=11, fontweight='bold')
        
        # Add value labels
        for i, mode in enumerate(modes):
            ax.text(i, means[mode] + sems[mode], f'{means[mode]:.1f}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Summary table in bottom row
    ax_table = fig.add_subplot(gs[2, :])
    ax_table.axis('tight')
    ax_table.axis('off')
    
    # Create summary statistics table
    summary_data = []
    for mode in ['fixed', 'adaptive']:
        mode_df = df[df['mode'] == mode]
        row = [
            'Fixed Timer' if mode == 'fixed' else 'Adaptive',
            len(mode_df),
            f"{mode_df['test_score'].mean():.1f}" if 'test_score' in mode_df else 'N/A',
            f"{mode_df['sus_score'].mean():.1f}" if 'sus_score' in mode_df else 'N/A',
            f"{mode_df['fatigue_rating'].mean():.2f}" if 'fatigue_rating' in mode_df else 'N/A',
            f"{mode_df['concentration'].mean():.2f}" if 'concentration' in mode_df else 'N/A'
        ]
        summary_data.append(row)
    
    table = ax_table.table(cellText=summary_data,
                          colLabels=['Mode', 'N', 'Test Score', 'SUS Score', 'Fatigue', 'Concentration'],
                          cellLoc='center',
                          loc='center',
                          bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2)
    
    # Style header
    for i in range(6):
        table[(0, i)].set_facecolor('#4287f5')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.suptitle('AdaptiBreak: Comprehensive Results Comparison', 
                fontsize=18, fontweight='bold', y=0.98)
    
    plt.savefig('analysis_comprehensive.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: analysis_comprehensive.png")


def generate_statistical_report(df):
    """Generate detailed statistical comparison report."""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("ADAPTIBREAK STATISTICAL ANALYSIS REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Sample info
    report_lines.append("SAMPLE INFORMATION")
    report_lines.append("-" * 80)
    report_lines.append(f"Total Sessions: {len(df)}")
    report_lines.append(f"  Fixed Mode: {len(df[df['mode'] == 'fixed'])}")
    report_lines.append(f"  Adaptive Mode: {len(df[df['mode'] == 'adaptive'])}")
    report_lines.append(f"Unique Participants: {df['participant_id'].nunique()}")
    report_lines.append("")
    
    # Test performance
    report_lines.append("TEST PERFORMANCE")
    report_lines.append("-" * 80)
    
    for mode in ['fixed', 'adaptive']:
        mode_df = df[df['mode'] == mode].dropna(subset=['test_score'])
        if len(mode_df) > 0:
            mode_name = 'Fixed Timer' if mode == 'fixed' else 'Adaptive'
            report_lines.append(f"{mode_name}:")
            report_lines.append(f"  Mean: {mode_df['test_score'].mean():.2f}%")
            report_lines.append(f"  SD: {mode_df['test_score'].std():.2f}")
            report_lines.append(f"  Range: [{mode_df['test_score'].min():.1f}, {mode_df['test_score'].max():.1f}]")
    
    # T-test
    fixed_scores = df[df['mode'] == 'fixed']['test_score'].dropna()
    adaptive_scores = df[df['mode'] == 'adaptive']['test_score'].dropna()
    
    if len(fixed_scores) > 0 and len(adaptive_scores) > 0:
        t_stat, p_value = stats.ttest_ind(fixed_scores, adaptive_scores)
        report_lines.append(f"\nIndependent t-test:")
        report_lines.append(f"  t-statistic: {t_stat:.4f}")
        report_lines.append(f"  p-value: {p_value:.4f}")
        report_lines.append(f"  Result: {'Significant' if p_value < 0.05 else 'Not significant'} (α=0.05)")
    report_lines.append("")
    
    # SUS Scores
    report_lines.append("SYSTEM USABILITY SCALE (SUS)")
    report_lines.append("-" * 80)
    
    for mode in ['fixed', 'adaptive']:
        mode_df = df[df['mode'] == mode].dropna(subset=['sus_score'])
        if len(mode_df) > 0:
            mode_name = 'Fixed Timer' if mode == 'fixed' else 'Adaptive'
            mean_sus = mode_df['sus_score'].mean()
            report_lines.append(f"{mode_name}:")
            report_lines.append(f"  Mean: {mean_sus:.2f}")
            report_lines.append(f"  SD: {mode_df['sus_score'].std():.2f}")
            
            # Interpretation
            if mean_sus >= 80.3:
                interpretation = "Excellent (A)"
            elif mean_sus >= 68:
                interpretation = "Good (B)"
            elif mean_sus >= 51:
                interpretation = "OK (C)"
            else:
                interpretation = "Poor (F)"
            report_lines.append(f"  Grade: {interpretation}")
    report_lines.append("")
    
    # Fatigue ratings
    report_lines.append("SUBJECTIVE FATIGUE RATINGS")
    report_lines.append("-" * 80)
    
    for mode in ['fixed', 'adaptive']:
        mode_df = df[df['mode'] == mode].dropna(subset=['fatigue_rating'])
        if len(mode_df) > 0:
            mode_name = 'Fixed Timer' if mode == 'fixed' else 'Adaptive'
            report_lines.append(f"{mode_name}:")
            report_lines.append(f"  Fatigue: {mode_df['fatigue_rating'].mean():.2f} (1-5)")
            report_lines.append(f"  Concentration: {mode_df['concentration'].mean():.2f} (1-5)")
            report_lines.append(f"  Alertness: {mode_df['alertness'].mean():.2f} (1-5)")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    
    # Save report
    report_text = "\n".join(report_lines)
    with open('analysis_report.txt', 'w') as f:
        f.write(report_text)
    
    print("\n" + report_text)
    print("\n✓ Saved: analysis_report.txt")


def main():
    """Main analysis function."""
    print("\n" + "=" * 80)
    print("AdaptiBreak - Data Analysis & Visualization")
    print("=" * 80 + "\n")
    
    # Load data
    df = load_all_data()
    
    if df is None or len(df) == 0:
        print("\n❌ No data available for analysis.")
        print("   Complete some study sessions first using main.py")
        return
    
    print("\nGenerating visualizations...\n")
    
    # Create output directory
    os.makedirs('analysis_output', exist_ok=True)
    os.chdir('analysis_output')
    
    # Generate plots
    try:
        plot_test_performance(df)
        plot_fatigue_ratings(df)
        plot_sus_scores(df)
        plot_biometric_fatigue(df)
        plot_overall_comparison(df)
        generate_statistical_report(df)
        
        print("\n" + "=" * 80)
        print("Analysis Complete!")
        print("=" * 80)
        print(f"\nAll outputs saved in: {os.getcwd()}")
        print("\nGenerated files:")
        print("  • analysis_test_performance.png - Test score comparison")
        print("  • analysis_fatigue_ratings.png - Subjective fatigue measures")
        print("  • analysis_sus_scores.png - Usability scores")
        print("  • analysis_biometric_fatigue.png - Detected fatigue patterns")
        print("  • analysis_comprehensive.png - Overall comparison")
        print("  • analysis_report.txt - Statistical report")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

