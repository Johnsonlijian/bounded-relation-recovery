function r03_zhang_cufsm_run(chunk_id, n_chunks)
% Independent reconstruction of Zhang et al. Table 4/Table 8 local-buckling cells.
% Usage from project root:
%   octave-cli --no-gui --quiet --eval "addpath('external_sources/zhang_reconstruction'); r03_zhang_cufsm_run(1,4)"
% The source article does not publish native CUFSM model files or the batch E;
% geometry is rebuilt from published ratios and one frozen effective modulus.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/analysis/cFSM']);
addpath([repo '/cutwp']); addpath([repo '/helpers']); addpath([repo '/interface']);
addpath([repo '/plotters']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
case_file = [root '/external_sources/zhang_reconstruction/zhang_cases_numeric.csv'];
raw = dlmread(case_file, ',', 1, 0);
N = rows(raw); lo = floor((chunk_id-1)*N/n_chunks)+1; hi = floor(chunk_id*N/n_chunks);
if hi < lo; return; end
out_file = sprintf('%s/outputs/r03_zhang_reconstruction_chunk_%02d.csv', root, chunk_id);
fid = fopen(out_file,'w');
fprintf(fid,'case_id,table,is_complex,a_over_t,a_over_b,c_over_a,source_stress_mpa,reconstructed_stress_mpa,relative_error_pct,length_at_min_mm,node_count,element_count,mesh_target_mm,effective_modulus_mpa,status\n');
E = 217400; nu = 0.30; t = 2.0; target = 4.0; nlengths = 32; neigs = 1;
length_factors = logspace(log10(0.30),log10(1.60),nlengths)';
springs=0; constraints=0; BC='S-S';
GBTcon.glob=0; GBTcon.dist=0; GBTcon.local=0; GBTcon.other=0; GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
for row = lo:hi
  case_id=raw(row,1); is_complex=raw(row,2); at=raw(row,3); ab=raw(row,4); cf=raw(row,5); source=raw(row,6);
  a = t*at; b = a/ab; c = a*cf; d = 0.5*c;
  [prop,node,elem] = r03_make_model(a,b,c,d,t,E,nu,target,is_complex);
  lengths = a*length_factors; m_all=cell(length(lengths),1); for ii=1:length(lengths); m_all{ii}=1; end
  [curve,~] = stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,neigs);
  first=zeros(length(curve),1); for ii=1:length(curve); first(ii)=curve{ii}(1,2); end
  [reconstructed,ix] = min(first); Lstar=lengths(ix);
  if ix>1 && ix<length(first)
    xx=log(lengths(ix-1:ix+1)); yy=first(ix-1:ix+1); pp=polyfit(xx,yy,2);
    if pp(1)>0
      x0=-pp(2)/(2*pp(1));
      if x0>=xx(1) && x0<=xx(3); reconstructed=polyval(pp,x0); Lstar=exp(x0); end
    end
  end
  relpct=(reconstructed/source-1)*100;
  if is_complex; tbl='Table 8'; else; tbl='Table 4'; end
  fprintf(fid,'%d,%s,%d,%.6g,%.6g,%.6g,%.9g,%.9g,%.9g,%.9g,%d,%d,%.6g,%.9g,ok\n',case_id,tbl,is_complex,at,ab,cf,source,reconstructed,relpct,Lstar,rows(node),rows(elem),target,E);
  fprintf('chunk=%d row=%d/%d case=%d table=%s at=%g ab=%g c/a=%g source=%g recon=%g err=%+.3f%% L=%g nodes=%d\n',chunk_id,row,hi,case_id,tbl,at,ab,cf,source,reconstructed,relpct,Lstar,rows(node)); fflush(stdout);
end
fclose(fid);
endfunction

function [prop,node,elem] = r03_make_model(a,b,c,d,t,E,nu,target,is_complex)
  if is_complex
    P=[c,b-d; c,b; 0,b; 0,0; a,0; a,c; a-d,c];
  else
    P=[c,b; 0,b; 0,0; a,0; a,c];
  end
  coords=[];
  for s=1:(rows(P)-1)
    p0=P(s,:); p1=P(s+1,:); n=max(1,ceil(norm(p1-p0)/target));
    for j=0:(n-1); coords=[coords; p0+(p1-p0)*(j/n)]; end
  end
  coords=[coords; P(end,:)]; nn=rows(coords);
  node=[(1:nn)' coords ones(nn,4)]; node(:,8)=1;
  elem=[(1:(nn-1))' (1:(nn-1))' (2:nn)' repmat(t,nn-1,1) repmat(100,nn-1,1)];
  prop=[100 E E nu nu E/(2*(1+nu))];
endfunction
