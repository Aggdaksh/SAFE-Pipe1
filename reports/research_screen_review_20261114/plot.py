"""Render the descriptive review figure from analysis.json; no experiments."""
import json
import os
from pathlib import Path
from statistics import median
import tempfile

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'safe-pipe-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
a=json.loads((HERE/'analysis.json').read_text())
labels=['Fixed: w2_t2_1g','Fixed: w2_t2_2g',
        'Uniform sample','Uniform + scaled memory','Partition-tail + scaled memory']
metrics=[a['fixed_configs'][c]['engine_regret_percent_on_10_complete_instances']
         for c in ('w2_t2_1g','w2_t2_2g')]
metrics += [a['methods'][m]['engine_regret_percent'] for m in ('uniform','uniform_memory','partition_tail')]
fig, axes=plt.subplots(1,2,figsize=(14,6),gridspec_kw={'width_ratios':[1.4,1]})
fig.subplots_adjust(left=.24,right=.98,top=.84,bottom=.25,wspace=.34)
y=np.arange(len(labels))
for delta,key,label,color in [(-.17,'median','Median','#176b87'),(.17,'mean','Mean','#e89c3f')]:
    values=[m[key] for m in metrics]
    axes[0].barh(y+delta,values,height=.3,label=label,color=color)
    for pos,value in zip(y+delta,values):
        axes[0].text(value+.12,pos,f'{value:.2f}%',va='center',fontsize=9)
axes[0].set_yticks(y,labels,fontsize=10)
axes[0].invert_yaxis()
axes[0].set_xlim(0,12)
axes[0].set_xlabel('Extra full-engine runtime vs hindsight best (%)')
axes[0].set_title('Ranking quality: 10 complete instances',fontsize=12,pad=15)
axes[0].legend(loc='upper right',frameon=False)
cases=[c for c in a['cases'] if c['method']=='uniform_memory']
fixed=median(c['fixed_w2_t2_2g_full_lifecycle_seconds'] for c in cases)
sweep=median(c['one_probe_per_config_sweep_lifecycle_seconds']+c['shared_sample_preparation_seconds'] for c in cases)
axes[1].bar([0,1],[fixed,sweep],color=['#176b87','#bb4d4d'],width=.55)
axes[1].set_xticks([0,1],['One fixed full job\n(measured medians)','8-probe sweep + prep\n(estimated; no final job)'],fontsize=10)
for x,value in enumerate([fixed,sweep]):axes[1].text(x,value+.8,f'{value:.2f} s',ha='center',fontweight='bold')
axes[1].set_ylim(0,38)
axes[1].set_ylabel('Median lifecycle seconds across the same 10 instances')
axes[1].set_title('One-shot overhead is a major constraint',fontsize=12,pad=15)
for ax in axes:
    ax.spines[['top','right']].set_visible(False)
fig.suptitle('Completed screen: useful diagnostics, no proven online policy benefit',fontsize=16,x=.52)
fig.text(.02,.11,'Scope: 12 recipes, one generation seed, two repeats. Ranking statistics exclude two failed full-reference instances.\n'
                 'Fixed 1 GB is a strong speed comparator but had 2/24 unsuccessful full attempts across all 12 instances; fixed 2 GB had 24/24 successes.\n'
                 'Sweep estimate sums one median probe lifecycle per configuration plus shared preparation; controller and final execution are excluded.\n'
                 'Config IDs w/t/g denote workers, threads per worker, GB per worker. Source: 6c08ec9; post-hoc review. No significance or future safety claim.',fontsize=9,va='center')
fig.savefig(HERE/'screen_review.png',dpi=160)
fig.savefig(HERE/'screen_review.svg')
svg = HERE/'screen_review.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
plt.close(fig)
print(HERE/'screen_review.png')
