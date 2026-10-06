addpath('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm-git');
addpath('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm-git/analysis');
addpath('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm-git/analysis/cFSM');
addpath('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm-git/cutwp');
addpath('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm-git/helpers');
addpath('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm-git/interface');
addpath('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm-git/plotters');
addpath('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm_octave_compat/analysis');
which stripmain
load('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm-git/examples/2006_dsm_design_guide/files_and_scripts/cnolip_P.mat');
BC='S-S';
neigs=10;
m_all=cell(length(lengths),1);
for ii=1:length(lengths); m_all{ii}=1; end
if ~exist('GBTcon','var') || isempty(GBTcon)
  GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
end
[curve_rerun,shapes_rerun]=stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,neigs);
save('R:\IMUT_WORKPOOL\01_PROJECTS\NAS_DRIVE\IMUT\_r38plus\AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26\external_sources\cufsm_public_rerun/cnolip_P_rerun.mat','curve_rerun','shapes_rerun','prop','node','elem','lengths','BC','neigs');
EOF

