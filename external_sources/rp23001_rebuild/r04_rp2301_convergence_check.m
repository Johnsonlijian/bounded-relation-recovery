function r04_rp2301_convergence_check()
% R04 W2 convergence check: are the high-eta deviations sensitive to the wavelength
% grid or mesh density? Re-runs the worst cases (eta=12 D/B=0.25, eta=20 D/B=0.4)
% with a wider/denser wavelength grid and a finer mesh.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/analysis/cFSM']);
addpath([repo '/cutwp']); addpath([repo '/helpers']); addpath([repo '/interface']);
addpath([repo '/plotters']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
E = 203000; nu = 0.30; t = 1.0;
cases = {250, 250/12, 0.25*250/12, 12.0;   % eta=12, D/B=0.25
         250, 250/20, 0.40*250/20, 20.0};  % eta=20, D/B=0.40
configs = {36, 0.25, 2.0, 3.0;    % contract grid (baseline, as in main rebuild)
           64, 0.10, 4.0, 1.5;   % wider, denser grid, finer mesh
           96, 0.05, 6.0, 1.5};  % extreme grid
out_file = [root '/outputs/r04_rp2301_convergence_check.csv'];
fid = fopen(out_file,'w');
fprintf(fid,'eta,D_over_B,nlengths,len_lo_h,len_hi_h,mesh_mm,kw_fsm,kw_equation19,ratio\n');
springs=0; constraints=0; BC='S-S';
GBTcon.glob=0; GBTcon.dist=0; GBTcon.local=0; GBTcon.other=0; GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
for c = 1:rows(cases)
  H = cases{c,1}; B = cases{c,2}; D = cases{c,3}; eta = cases{c,4};
  kw_eq = 4 + 24*eta/(20 + 4.4*eta + eta^2);
  for k = 1:rows(configs)
    nlengths = configs{k,1}; llo = configs{k,2}; lhi = configs{k,3}; target = configs{k,4};
    [prop,node,elem] = r04_make_channel(H,B,D,t,E,nu,target);
    length_factors = logspace(log10(llo), log10(lhi), nlengths)';
    lengths = H*length_factors; m_all=cell(length(lengths),1); for ii=1:length(lengths); m_all{ii}=1; end
    [curve,~] = stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,1);
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
    fprintf(fid,'%.6g,%.6g,%d,%.3g,%.3g,%.3g,%.6g,%.6g,%.6g\n', eta, D/B, nlengths, llo, lhi, target, kw_fsm, kw_eq, ratio);
    fprintf('eta=%g grid=[%g,%g]h n=%d mesh=%g kw_fsm=%.4f ratio=%.4f\n', eta, llo, lhi, nlengths, target, kw_fsm, ratio); fflush(stdout);
  end
end
fclose(fid);
endfunction

function [prop,node,elem] = r04_make_channel(H,B,D,t,E,nu,target)
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