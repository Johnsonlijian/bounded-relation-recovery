function r04_rp2301_cufsm_run(chunk_id, n_chunks)
% R04 W2: independent CUFSM rebuild of lipped-channel sections inside the declared
% geometry domain of AISI RP23-01 (pure compression, no punchouts), for replay audit
% of the reported web plate buckling coefficient equation
%   k_w(eta) = 4 + 24*eta/(20 + 4.4*eta + eta^2),  eta = h/b, 1.2 <= eta <= 22.
% Usage from project root:
%   octave-cli --no-gui --quiet --eval "addpath('external_sources/rp23001_rebuild'); r04_rp2301_cufsm_run(1,3)"
% Boundary: these are fresh sections sampled in the declared domain, NOT the report's
% own 1228-section FSM library; the comparison tests the declared equation on an
% independently generated evidence set.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/analysis/cFSM']);
addpath([repo '/cutwp']); addpath([repo '/helpers']); addpath([repo '/interface']);
addpath([repo '/plotters']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
case_file = [root '/external_sources/rp23001_rebuild/rp23001_cases_numeric.csv'];
raw = dlmread(case_file, ',', 1, 0);
N = rows(raw); lo = floor((chunk_id-1)*N/n_chunks)+1; hi = floor(chunk_id*N/n_chunks);
if hi < lo; return; end
out_file = sprintf('%s/outputs/r04_rp2301_rebuild_chunk_%02d.csv', root, chunk_id);
fid = fopen(out_file,'w');
fprintf(fid,'case_id,H_mm,B_mm,D_mm,t_mm,eta_w,D_over_B,fcrl_mpa,kw_fsm,kw_equation19,ratio,nodes,status\n');
E = 203000; nu = 0.30; target = 3.0; nlengths = 36; neigs = 1;
% local wavelength grid: 0.25h .. 2.0h (log-spaced); quadratic interpolation at minimum
length_factors = logspace(log10(0.25), log10(2.0), nlengths)';
springs=0; constraints=0; BC='S-S';
GBTcon.glob=0; GBTcon.dist=0; GBTcon.local=0; GBTcon.other=0; GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
for row = lo:hi
  case_id=raw(row,1); H=raw(row,2); B=raw(row,3); D=raw(row,4); t=raw(row,5);
  eta=raw(row,6); doverb=raw(row,7);
  kw_eq = 4 + 24*eta/(20 + 4.4*eta + eta^2);
  [prop,node,elem] = r04_make_channel(H,B,D,t,E,nu,target);
  lengths = H*length_factors; m_all=cell(length(lengths),1); for ii=1:length(lengths); m_all{ii}=1; end
  [curve,~] = stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,neigs);
  first=zeros(length(curve),1); for ii=1:length(curve); first(ii)=curve{ii}(1,2); end
  [fcrl,ix] = min(first);
  if ix>1 && ix<length(first)
    xx=log(lengths(ix-1:ix+1)); yy=first(ix-1:ix+1); pp=polyfit(xx,yy,2);
    if pp(1)>0
      x0=-pp(2)/(2*pp(1));
      if x0>=xx(1) && x0<=xx(3); fcrl=polyval(pp,x0); end
    end
  end
  kw_fsm = fcrl*12*(1-nu^2)*(H/t)^2/(pi^2*E);
  ratio = kw_fsm/kw_eq;
  fprintf(fid,'%d,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.9g,%.9g,%.9g,%.9g,%d,ok\n', ...
    case_id,H,B,D,t,eta,doverb,fcrl,kw_fsm,kw_eq,ratio,rows(node));
  fprintf('chunk=%d row=%d/%d case=%d eta=%g D/B=%g kw_fsm=%.4f kw_eq=%.4f ratio=%.4f\n', ...
    chunk_id,row,hi,case_id,eta,doverb,kw_fsm,kw_eq,ratio); fflush(stdout);
end
fclose(fid);
endfunction

function [prop,node,elem] = r04_make_channel(H,B,D,t,E,nu,target)
% Centreline C-channel polyline: upper lip tip -> upper flange tip -> web -> lower
% flange tip -> lower lip tip (plate centreline coordinates, corner radii ignored).
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