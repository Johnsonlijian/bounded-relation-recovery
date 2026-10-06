function r03_ksce_spectrum_transfer()
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));repo=[root '/external_sources/cufsm-git'];
addpath(repo);addpath([repo '/analysis']);addpath([repo '/analysis/cFSM']);addpath([repo '/cutwp']);addpath([repo '/helpers']);addpath([repo '/interface']);addpath([repo '/plotters']);addpath([root '/external_sources/cufsm_octave_compat/analysis']);
raw=dlmread([root '/external_sources/zhang_reconstruction/ksce2023_cases_numeric.csv'],',',1,0); fid=fopen([root '/outputs/r03_ksce2023_spectrum_transfer.csv'],'w');
fprintf(fid,'case_id,a_mm,b_mm,c_mm,d_mm,source_sigma_crd_mpa,nearest_reconstructed_eigen_mpa,relative_error_pct,length_at_nearest_mm,eigen_rank,mesh_target_mm,effective_modulus_mpa,status\n');
E=217400;nu=.3;t=2;target=4;neigs=6;length_factors=logspace(log10(.30),log10(10),60)';m_all=cell(length(length_factors),1);for j=1:length(m_all);m_all{j}=1;end; springs=0;constraints=0;BC='S-S';GBTcon.glob=0;GBTcon.dist=0;GBTcon.local=0;GBTcon.other=0;GBTcon.ospace=1;GBTcon.couple=1;GBTcon.orth=2;GBTcon.norm=1;
for r=1:rows(raw);case_id=raw(r,1);a=raw(r,2);b=raw(r,3);c=raw(r,4);d=raw(r,5);source=raw(r,6);[prop,node,elem]=r03_make_model(a,b,c,d,t,E,nu,target);lengths=a*length_factors;m_all=cell(length(lengths),1);for j=1:length(lengths);m_all{j}=1;end;[curve,~]=stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,neigs); best=Inf;bestL=NaN;bestRank=NaN;for i=1:length(curve);vals=curve{i}(:,2);for k=1:length(vals);err=abs(vals(k)-source);if err<best;best=err;bestL=lengths(i);bestRank=k;bestVal=vals(k);end;end;end;relpct=(bestVal/source-1)*100;fprintf(fid,'%d,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%d,%.9g,%.9g,ok\n',case_id,a,b,c,d,source,bestVal,relpct,bestL,bestRank,target,E);fprintf('KSCE case=%d source=%g nearest=%g err=%+.2f%% L=%g eig=%d\n',case_id,source,bestVal,relpct,bestL,bestRank);fflush(stdout);end;fclose(fid);
endfunction
function [prop,node,elem]=r03_make_model(a,b,c,d,t,E,nu,target)
P=[c,b-d;c,b;0,b;0,0;a,0;a,c;a-d,c];coords=[];for s=1:(rows(P)-1);p0=P(s,:);p1=P(s+1,:);n=max(1,ceil(norm(p1-p0)/target));for j=0:(n-1);coords=[coords;p0+(p1-p0)*(j/n)];end;end;coords=[coords;P(end,:)];nn=rows(coords);node=[(1:nn)' coords ones(nn,4)];node(:,8)=1;elem=[(1:(nn-1))' (1:(nn-1))' (2:nn)' repmat(t,nn-1,1) repmat(100,nn-1,1)];prop=[100 E E nu nu E/(2*(1+nu))];
endfunction

