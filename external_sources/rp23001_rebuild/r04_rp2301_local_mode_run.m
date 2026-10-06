function r04_rp2301_local_mode_run(chunk_id, n_chunks)
% R04 W2 mode-predicate rerun.
% AISI RP23-01 Section 4 identifies the critical LOCAL buckling stress as the first
% local minimum of the signature curve, and states that a single minimum can be a
% distortional mode misread as local. The report therefore uses the two-step cFSM
% classification of Li and Schafer (2010). The first rebuild took the lowest
% unconstrained eigenvalue in 0.25h..2.0h. This rerun keeps the same geometry, mesh
% and length grid, and constrains the basis to local modes only
% (GBTcon.local = 1, global/distortional/other = 0).
% Usage:
%   octave-cli --no-gui --quiet --eval "addpath('external_sources/rp23001_rebuild'); r04_rp2301_local_mode_run(1,3)"
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/analysis/cFSM']);
addpath([repo '/cutwp']); addpath([repo '/helpers']); addpath([repo '/interface']);
addpath([repo '/plotters']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
raw = dlmread([root '/external_sources/rp23001_rebuild/rp23001_cases_numeric.csv'], ',', 1, 0);
N = rows(raw); lo = floor((chunk_id-1)*N/n_chunks)+1; hi = floor(chunk_id*N/n_chunks);
if hi < lo; return; end
out_file = sprintf('%s/outputs/r04_rp2301_local_mode_chunk_%02d.csv', root, chunk_id);
fid = fopen(out_file,'w');
fprintf(fid,'case_id,eta_w,D_over_B,fcrl_local_mpa,kw_local,kw_equation19,ratio_local,L_over_H,nlm,nodes,status\n');
E = 203000; nu = 0.30; target = 3.0; nlengths = 36;
length_factors = logspace(log10(0.25), log10(2.0), nlengths)';
springs=0; constraints=0; BC='S-S';
for row = lo:hi
  case_id=raw(row,1); H=raw(row,2); B=raw(row,3); D=raw(row,4); t=raw(row,5);
  eta=raw(row,6); doverb=raw(row,7);
  kw_eq = 4 + 24*eta/(20 + 4.4*eta + eta^2);
  [prop,node,elem] = r04_make_channel_local(H,B,D,t,E,nu,target);
  [~,~,~,~,~,~,~,ndm,nlm,~] = base_properties(node,elem);
  ngm = 4; nom = 2*(rows(node)-1);
  GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
  GBTcon.local=ones(1,nlm); GBTcon.dist=zeros(1,ndm);
  GBTcon.glob=zeros(1,ngm); GBTcon.other=zeros(1,nom);
  lengths = H*length_factors; m_all=cell(length(lengths),1);
  for ii=1:length(lengths); m_all{ii}=1; end
  [curve,~] = stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,1);
  first=zeros(length(curve),1);
  for ii=1:length(curve); first(ii)=curve{ii}(1,2); end
  [fcrl,ix] = min(first);
  if ix>1 && ix<length(first)
    xx=log(lengths(ix-1:ix+1)); yy=first(ix-1:ix+1); pp=polyfit(xx,yy,2);
    if pp(1)>0
      x0=-pp(2)/(2*pp(1));
      if x0>=xx(1) && x0<=xx(3); fcrl=polyval(pp,x0); end
    end
  end
  kw_local = fcrl*12*(1-nu^2)*(H/t)^2/(pi^2*E);
  ratio = kw_local/kw_eq;
  fprintf(fid,'%d,%.6g,%.6g,%.9g,%.9g,%.9g,%.9g,%.6g,%d,%d,ok\n', ...
    case_id,eta,doverb,fcrl,kw_local,kw_eq,ratio,lengths(ix)/H,nlm,rows(node));
  fflush(fid);
  fprintf('local chunk=%d case=%d eta=%g D/B=%g kw_local=%.4f kw_eq=%.4f ratio=%.4f L/H=%.3f\n', ...
    chunk_id,case_id,eta,doverb,kw_local,kw_eq,ratio,lengths(ix)/H); fflush(stdout);
end
fclose(fid);
endfunction

function [prop,node,elem] = r04_make_channel_local(H,B,D,t,E,nu,target)
  P=[B, H-D; B, H; 0, H; 0, 0; B, 0; B, D];
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
