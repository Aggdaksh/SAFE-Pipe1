import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

export async function build(root) {
  const dir = path.join(root, 'docs/minor_report_v1/academic_report');
  const pack = path.dirname(dir);
  const draft = await fs.readFile(path.join(pack, 'REPORT_DRAFT.md'), 'utf8');
  const register = JSON.parse(await fs.readFile(path.join(pack, 'figure_register.json'), 'utf8'));
  const metrics = JSON.parse(await fs.readFile(path.join(pack, 'verified_facts.json'), 'utf8'));
  const dataset = JSON.parse(await fs.readFile(path.join(root, 'configs/datasets_main_v1.json'), 'utf8'));
  const configs = JSON.parse(await fs.readFile(path.join(root, 'configs/dask_grid.json'), 'utf8')).configs;
  const primaryFigures = ['F01_architecture','F05_grouped_split','F11_pressure_design','F10_advisor_candidates','F06_prediction_scatter','F08_upper_coverage','F18_screen_regret','F12_stage_a','F13_stage_b_fidelity','F14_probe_cost','F15_worker_memory','F16_closed_gate'];
  const figureMap = Object.fromEntries(primaryFigures.map((id,i)=>[id.split('_')[0],`Figure ${i+1}`]));
  Object.assign(figureMap,{F02:'Table 3',F03:'Table 2',F04:'Figure 14',F07:'Table 6',F09:'Table 7',F17:'Table 5'});
  const clean = text => text.replace(/F06[–-]F08/g,'Figures 5 and 6').replace(/\bF\d{2}\b/g, x => figureMap[x] || x).replace(/[—–]/g,'-').replace(/\*\*Use .*?\*\*/g,'').replace(/\*\*/g,'').replace(/`([^`]+)`/g,'$1').trim();
  const blocks = [];
  const p = text => blocks.push({type:'paragraph',text:clean(text)});
  const heading = (text,level=2) => blocks.push({type:'heading',level,text});
  const figure = (id) => {
    const f = register.find(x=>x.id===id);
    blocks.push({type:'figure',id,file:path.join(pack,'figures',id+'.png'),title:f.title,caption:f.caption.replace(/[—–]/g,'-'),source:f.sources.join('; ')+' [7]'});
  };
  const table = (number,title,headers,rows,widths) => blocks.push({type:'table',number,title,headers,rows,widths});
  const references = [
    {n:1,text:'M. Rocklin, “Dask: Parallel Computation with Blocked algorithms and Task Scheduling,” Proceedings of the 14th Python in Science Conference, pp. 126–132, 2015. DOI: 10.25080/majora-7b98e3ed-013.',url:'https://doi.org/10.25080/majora-7b98e3ed-013'},
    {n:2,text:'S. Venkataraman, Z. Yang, M. Franklin, B. Recht and I. Stoica, “Ernest: Efficient Performance Prediction for Large-Scale Advanced Analytics,” 13th USENIX Symposium on Networked Systems Design and Implementation, pp. 363–378, 2016.',url:'https://www.usenix.org/conference/nsdi16/technical-sessions/presentation/venkataraman'},
    {n:3,text:'J. Will, L. Thamsen, D. Scheinert, J. Bader and O. Kao, “C3O: Collaborative Cluster Configuration Optimization for Distributed Data Processing in Public Clouds,” arXiv:2107.13317, 2021.',url:'https://arxiv.org/abs/2107.13317'},
    {n:4,text:'G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye and T.-Y. Liu, “LightGBM: A Highly Efficient Gradient Boosting Decision Tree,” Advances in Neural Information Processing Systems 30, pp. 3146–3154, 2017.',url:'https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html'},
    {n:5,text:'A. N. Angelopoulos and S. Bates, “A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification,” arXiv:2107.07511, 2021, revised December 2022.',url:'https://arxiv.org/abs/2107.07511'},
    {n:6,text:'Dask Developers, “Worker Memory Management,” Dask.distributed 2026.8.0 documentation. Accessed 22 November 2026.',url:'https://distributed.dask.org/en/stable/worker-memory.html'},
    {n:7,text:'SAFE-Pipe project team, “SAFE-Pipe source code and experimental artifacts,” Aggdaksh/SAFE-Pipe1, original-advisor evidence revision caa8a8a and separate research evidence revision edef1cd, 2026. Repository artifacts include the original audited table, fitted predictions, Stage A/B summaries and worker-memory export.',url:'https://github.com/Aggdaksh/SAFE-Pipe1'}
  ];
  const literature = () => {
    heading('2 BACKGROUND AND RELATED WORK',1);
    heading('2.1 Data processing tasks and resource configurations');
    p('A task is a schedulable unit of computation, while a job in this report denotes the complete requested workload. A task graph expresses dependencies between the units. Workers execute tasks using their configured threads; partitions divide the input into portions. Dask represents parallel computations through task dependencies and blocked algorithms [1]. The measured SAFE-Pipe backend uses multiple worker processes on one Windows computer, not a multi-node cluster.');
    p('A memory cap applies separately to a worker. Two workers capped at 1 GB each are not equivalent to one worker capped at 2 GB, even though their total configured memory is equal. Process RSS, managed objects and spilled data describe different quantities. Dask distinguishes managed and process memory and can spill, pause and restart workers in response to pressure [6]. The thresholds observed in each experiment must therefore be read from the recorded settings, rather than inferred from the cap alone.');
    heading('2.2 Runtime prediction and configuration selection');
    p('Ernest builds performance models from sampled job executions and uses experimental design to reduce the observations needed for prediction [2]. It motivates learning a relationship between workload scale, configuration and runtime. Its sampled measurements are an investment whose usefulness depends on the job and deployment setting. SAFE-Pipe instead begins with a frozen, exhaustive local grid. Its later probe investigation tests whether additional execution information repays its cost for short jobs; it does not reproduce Ernest or compare against its implementation.');
    p('C3O uses shared historical runtime data and regression models to support cluster configuration selection across execution contexts [3]. This provides a relevant example of history-based advice. SAFE-Pipe uses a much narrower data collection: four fixed profiles on one host, without collaborative cross-user history or a broad transfer claim. The related systems establish that resource selection is an existing research area; SAFE-Pipe does not claim to invent configuration tuning.');
    heading('2.3 Gradient boosted runtime modelling');
    p('LightGBM is an implementation of gradient-boosted decision trees designed for efficient learning from structured features [4]. In SAFE-Pipe it is used as a regression model for log successful engine runtime. Workload descriptors and candidate resource settings form the input, while measured runtime is the target. The particular SAFE-Pipe fit is small and uses fixed hyperparameters. It does not establish the training-speed or benchmark-accuracy claims of the LightGBM paper on this project dataset.');
    heading('2.4 Uncertainty and scope control');
    p('Conformal prediction provides a framework for calibrating prediction sets or bounds using held-out conformity scores under stated assumptions [5]. SAFE-Pipe uses grouped calibration residuals to construct a one-sided upper runtime estimate. Its small, fixed-profile evaluation is not evidence of universal coverage. Candidate selection, changes of input profile and changes of hardware require their own assessment; a nominal calibration target is not automatically a job-success probability.');
    p('Support checks complement runtime estimates by refusing descriptors outside the frozen evidence contract. Such abstention is useful when data are limited, but the current exact descriptor check is not a learned measure of distance or a proof that actual input contents and hardware match. Those boundaries are part of the system specification.');
    table(1,'Comparison of related approaches and the present scope',['Work','Main approach','Relationship to SAFE-Pipe'],[
      ['Dask [1]','Task graphs and blocked parallel computation','Execution substrate; SAFE-Pipe adds bounded pre-run advice.'],
      ['Ernest [2]','Performance modelling from sample executions','Motivates profiling; no reproduced Ernest baseline is claimed.'],
      ['C3O [3]','Shared runtime histories for cluster selection','Broader execution contexts than the single-host study.'],
      ['LightGBM [4]','Gradient-boosted decision-tree learning','Runtime regression component, not a project novelty claim.'],
      ['Conformal prediction [5]','Calibration of predictive uncertainty','Basis for an upper estimate with explicit small-sample limits.']
    ],[.17,.34,.49]);
    heading('2.5 Research question addressed by this project');
    p('The engineering question is whether transparent, constrained advice can be made reproducible within a deliberately bounded workload and configuration contract. The subsequent research question is whether small execution probes preserve useful full-input pressure information and add value beyond stronger metadata rules. The experiments answer parts of these questions descriptively. They do not demonstrate superiority to the related systems, establish a new general selector, or validate an online probing policy.');
  };
  const chunks = draft.slice(draft.indexOf('## 1. Introduction')).split(/\n\n+/);
  let chapter = 0;
  for (let chunk of chunks) {
    if (chunk.startsWith('## Evidence and reference')) break;
    if (chunk.startsWith('## 2. Background')) {literature();chapter=2;continue;}
    if (chapter===2 && !chunk.startsWith('## 3.')) continue;
    if (chunk.startsWith('## ')) {
      const match = chunk.match(/^## (\d+)\. (.*)/);
      if (!match) continue;
      chapter=Number(match[1]); heading(`${chapter} ${match[2].replace(/ —.*$/,'').toUpperCase()}`,1);
      continue;
    }
    if (chunk.startsWith('### ')) {
      const t=chunk.slice(4).replace(/—/g,'-'); heading(t);
      if(t.startsWith('7.1')) table(6,'Original held-out runtime results',['Measure','Observed result','Denominator or interpretation'],[
        ['LightGBM MdAPE','13.84%','24 held-out rows across 8 groups'],['Family-median baseline MdAPE','23.01%','Same 24 test rows'],['Upper coverage by row','24 / 24','Observed coverage only'],['Upper coverage by group','8 / 8','Not a future guarantee'],['Mean point-to-upper width','1.33 seconds','Saved test-set average']],[.42,.22,.36]);
      if(t.startsWith('7.2')) table(7,'Historical policy comparison using the original table',['Rule','Mean median normalized cost'],[['Historical policy','7.524'],['Declared reference w1_t1_2g','11.421'],['Conservative configuration','10.366'],['Uniform random selection','8.950']],[.68,.32]);
      continue;
    }
    if(chunk.startsWith('**Use ') || chunk.startsWith('**Related-work')) continue;
    if(chunk.startsWith('```')) {
      const lines=chunk.split('\n').slice(1,-1);
      for(const equation of lines) if(equation.trim()) blocks.push({type:'equation',text:equation.replaceAll('*','×').replaceAll('lambda','λ').replaceAll('beta','β')});
      continue;
    }
    chunk=chunk.replace(/\n/g,' ');
    if(chunk.startsWith('For report production,') || chunk.startsWith('The previously discussed approximately 6.78 GiB')) continue;
    chunk=chunk.replace('Do not silently change fitted feature values to make the unit labels look more convenient; refer to docs/DATA_DICTIONARY.md.','The fitted feature contract is retained to preserve compatibility with the saved model; units are documented in the data dictionary.');
    chunk=chunk.replace(/The artifact preserves held-out predictions and metrics, but no saved epoch-by-epoch training history or training-accuracy metric\./,'The saved artifact contains held-out predictions and metrics; an iteration-wise training history was not retained.');
    chunk=chunk.replace('The advisor_demo.html page is a viewer for those saved outputs, not a screenshot of a finished product interface.','Appendix A presents a viewer of saved inference output, rather than a finished product interface.');
    chunk=chunk.replace('For report production,','For final delivery,');
    chunk=chunk.replace('No model was retrained to build this report.','The reported metrics use the saved model without retraining.');
    chunk=chunk.replace('These are declared preferences, not trained coefficients or a proven universally optimal formula.','These coefficients express declared preferences; they are not fitted parameters or a universally optimal formula.');
    if(chapter===1 && chunk.startsWith('SAFE-Pipe addresses')) chunk+=' Dask supplies the task-graph execution model [1].';
    if(chunk.startsWith('LightGBM predicts log successful')) chunk+=' The prediction and calibration components follow the methodological background in [4] and [5].';
    p(chunk);
    if(chapter===3 && chunk.startsWith('The model feature whitelist')) {
      blocks.push({type:'equation',text:'MdAPE = 100 × median_i (|t̂_i - t_i| / t_i)'});
      p('Here t_i is the observed engine runtime and t̂_i is its point prediction. MdAPE summarizes relative prediction error; it is not classification accuracy.');
    }
    if(chapter===4 && chunk.startsWith('The original offline path')) figure('F01_architecture');
    if(chapter===5 && chunk.startsWith('The four fixed original datasets')) {
      const labels={scan_filter:'Scan/filter',groupby:'Group-by',skewed_join:'Skewed join',sort_merge:'Key shuffle (sort_merge)'};
      const deadlines={scan_filter:'2.6',groupby:'7.9',skewed_join:'4.3',sort_merge:'13.1'};
      table(2,'Original synthetic workload inventory',['Profile','Rows in millions','Parquet MB','Engine deadline s'],dataset.map(d=>[labels[d.family],(d.n_rows/1e6).toFixed(2),(d.input_bytes/1e6).toFixed(2),deadlines[d.family]]),[.38,.22,.22,.18]);
      table(3,'Original eight configuration candidates',['Configuration','Workers','Threads per worker','Cap per worker'],configs.map(c=>[c.config_id,String(c.n_workers),String(c.threads_per_worker),c.memory_limit]),[.34,.17,.27,.22]);
    }
    if(chapter===5 && chunk.startsWith('The grouped split')) figure('F05_grouped_split');
    if(chapter===5 && chunk.startsWith('LightGBM predicts')) table(4,'Model and calibration specification',['Component','Frozen setting'],[['Target','Log successful engine runtime'],['LightGBM trees / leaves','120 trees / 7 leaves'],['Learning rate / minimum child','0.05 / 3'],['L2 regularization','1'],['Train / calibrate / test','36 / 36 / 24 rows; 12 / 12 / 8 groups'],['Upper log offset','0.523642; nominal calibration alpha 0.1']],[.42,.58]);
    if(chapter===5 && chunk.startsWith('Stage A separated')) figure('F11_pressure_design');
    if(chapter===6 && chunk.startsWith('Four current inference-only')) figure('F10_advisor_candidates');
    if(chapter===6 && chunk.startsWith('On the separate research branch')) table(5,'Software verification scopes',['Implementation','Recorded result','Meaning'],[['Original advisor d6f906a','143 passed; 0 failed/errors/skipped','Full Windows suite including tiny Dask fixtures; 36.89 s.'],['Separate research prototype','38 targeted tests passed','8 default and 24 counterfactual decisions; 37 termination records checked.']],[.30,.30,.40]);
    if(chapter===7 && chunk.startsWith('On the 24 saved held-out')) figure('F06_prediction_scatter');
    if(chapter===7 && chunk.startsWith('The stored upper estimates')) figure('F08_upper_coverage');
    if(chapter===7 && chunk.startsWith('The earlier development screen')) figure('F18_screen_regret');
    if(chapter===7 && chunk.startsWith('Stage A recorded')) figure('F12_stage_a');
    if(chapter===7 && chunk.startsWith('Stage B recorded')) {
      figure('F13_stage_b_fidelity');
      table(8,'Distinct experimental denominators',['Study','Attempts','Outcomes and scope'],[['Original main-v1','96','96 success; 4 profiles x 8 configurations x 3 repeats.'],['Earlier research screen','768','759 success, 1 timeout, 8 execution errors; 12 recipes.'],['Stage A full attempts','48','41 success and 7 execution errors; 8 instances.'],['Stage B probes','96','96 quiet successes; 8/32 pressure-discrepancy groups.']],[.30,.15,.55]);
    }
    if(chapter===7 && chunk.startsWith('The existing one-probe')) {
      figure('F14_probe_cost');
      table(9,'Constructed historical request cost comparison',['Rule','Median total s','Selected successes'],[['Fixed 2 GB','4.96','24 / 24'],['Size-aware metadata','4.79','24 / 24'],['Always one probe','10.37','24 / 24'],['Ambiguous-only probe','7.38','24 / 24'],['Guarded default with probe disabled','4.79','24 / 24']],[.50,.23,.27]);
      p('The success denominator is the set of unique selected historical full outcomes, not independent prospective policy requests. Costs are constructed across sessions and exclude unmeasured metadata/controller overhead.');
    }
    if(chapter===7 && chunk.startsWith('The existing export preserves')) figure('F15_worker_memory');
    if(chapter===8 && chunk.startsWith('SAFE-Pipe demonstrates')) figure('F16_closed_gate');
  }
  heading('REFERENCES',1);
  for(const r of references) p(`[${r.n}] ${r.text} ${r.url}`);
  heading('APPENDIX A SAVED ADVISOR OUTPUT',1);
  p('The image below presents actual saved JSON from inference on the original Windows environment. It is an evidence viewer, not a finished product interface. The balanced example selects w2_t2_1g for the fixed sort_merge profile at a 13.1-second engine deadline. The point estimate is approximately 2.29 seconds and the upper estimate approximately 3.87 seconds. These are predictions rather than fresh execution measurements.');
  blocks.push({type:'figure',id:'saved_advisor_output',file:path.join(pack,'screenshots/saved_advisor_output.png'),title:'Saved balanced advisor inference output',caption:'Actual captured inference output presented in a report viewer. No Dask workload was executed for the capture.',source:'advisor_capture/sort_balanced.json and screenshots/saved_advisor_output.png [7]'});
  heading('APPENDIX B ORIGINAL REPEAT RANGES',1);
  p('The following figure preserves the per-configuration repeat ranges from the original study. The bars show observed minimum and maximum over three repetitions, not confidence intervals. Each family panel uses its own horizontal scale. These data are retained separately from the later research studies.');
  figure('F04_runtime_ranges');
  heading('APPENDIX C REPRODUCIBILITY AND EVIDENCE IDENTITY',1);
  p('The original source table is data/curated/runs.csv. Model predictions and metrics are in artifacts/main_v1/. Workload and configuration definitions are frozen under configs/. The original-advisor Windows software receipt records implementation d6f906a and is published in evidence commit caa8a8a. Separate research findings are read from revision edef1cd; report asset production is committed in 05d3e66. The report does not merge research code or turn its disabled policy into an enabled controller.');
  p('The file docs/minor_report_v1/source_manifest.json pins compact input paths and LF-normalized SHA-256 hashes. A structured source check confirms the 78 original verified source/evidence hashes. Original generated Parquet, raw diagnostics, local credentials and virtual environments are kept outside the shareable report package. The later worker-memory export preserves restarted lifetimes and missing-value distinctions.');
  p('The recorded software command was .venv/Scripts/python.exe -m experiments.verify_main_validation --out reports/main_validation_windows_checks_v1. It is documented for reproducibility, not repeated as part of report generation. Fresh validation needs its own new study directory and a reviewed frozen plan; the existing evidence folder must not be overwritten.');
  p('In the earlier development screen, approximately 6.78 GiB referred to prepared Parquet/sample storage across two screen directories. It was not the size of one original training dataset or the saved LightGBM model.');
  const abstract = draft.split('## Abstract — first draft')[1].split('## 1. Introduction')[0].trim().replaceAll('—','-');
  const output = {
    title:'SAFE-Pipe: Failure-Aware Cost and Runtime Optimization of Distributed Data Pipelines under SLA Constraints',
    team:[['Daksh Aggarwal','23/IT/047'],['Ganant Awasthi','23/IT/055'],['Chaitanya Singh','23/IT/045']],
    guide:'Prof. Dinesh Kumar Vishwakarma',designation:'Head of Department',department:'Department of Information Technology',institution:'Delhi Technological University',semester:'B.Tech VII Semester',session:'2026-2027',date:'NOVEMBER 2026',
    logo:path.join(dir,'DTU_logo.png'),abstract,blocks,references,
    planned_figures:blocks.filter(b=>b.type==='figure').length,
    planned_tables:blocks.filter(b=>b.type==='table').length,
    underlying_facts_sha256:crypto.createHash('sha256').update(JSON.stringify(metrics)).digest('hex')
  };
  await fs.writeFile(path.join(dir,'report_content.json'),JSON.stringify(output,null,2)+'\n');
  await fs.writeFile(path.join(dir,'references.json'),JSON.stringify(references,null,2)+'\n');
  await fs.writeFile(path.join(dir,'format_contract.md'),`# Academic report production contract\n\nReference: the user supplied DTU Information Technology minor report and the Siddharth Yash BTech report PDFs, retained unchanged outside the repository. The IT report controls the department-specific cover and front-matter pattern.\n\nA4 portrait; 1 inch margins; Times New Roman 12 point body; black 14 point chapter headings; 1.5 line spacing; justified prose. Cover is centered with a DTU seal rendered directly from the supplied IT sample. Front matter has separate declaration, certificate, acknowledgement, abstract, contents, figure list, table list and abbreviation pages. The cover is unnumbered, front matter uses lower-case Roman numbers, and the main text restarts with Arabic 1. Native editable text, tables, equation objects, captions and navigation fields are required. Figures are embedded images; their vector originals remain in the report pack.\n\nIdentity follows the user's supplied team list and latest Prof designation, rather than older synopsis wording. Candidate and supervisor signature/date lines remain blank. The report contains the completed local prototype, later research evidence, measured limitations and future work; it does not claim the fresh 96-cell study ran. No signatures, approval, new benchmarks or training are generated.\n\nDocument creation and rendering use installed Microsoft Word 16 through its native automation API because the managed Python document runtime and its loader are unavailable. Project environments are unchanged. The source PDFs are not modified.\n`);
  return {blocks:blocks.length,figures:output.planned_figures,tables:output.planned_tables,output:path.join(dir,'report_content.json')};
}
