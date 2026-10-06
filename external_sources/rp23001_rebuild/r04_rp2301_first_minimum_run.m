function r04_rp2301_first_minimum_run()
% R04 W2 signature-curve selector, matching AISI RP23-01 Section 4:
% when two local minima exist, the critical LOCAL mode is the first
% (shortest-wavelength) local minimum, not the lowest eigenvalue.
% Unconstrained stripmain, same sharp-corner centreline sections as the
% first rebuild. Records every interior local minimum so the selector
% can be audited. This is not a cFSM-constrained eigenvalue.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/analysis/cFSM']);
addpath([repo '/cutwp']); addpath([repo '/helpers']); addpath([repo '/interface']);
addpath([repo '/plotters']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
warning('off','all');
raw = dlmread([root '/external_sources/rp23001_rebuild/rp23001_cases_numeric.csv'], ',', 1, 0);
out_file = [root '/outputs/r04_rp2301_first_minimum.csv'];
fid = fopen(out_file,'w');
fprintf(fid,'case_id,eta_w,D_over_B,n_minima,kw_lowest,L_over_H_lowest,kw_first_min,L_over_H_first,kw_equation19,ratio_lowest,ratio_first,status\n');
E = 203000; nu = 0.30; target = 3.0; nlengths = 48;
length_factors = logspace(log10(0.20), log10(3.0), nlengths)';
springs=0; constraints=0; BC='S-S';
GBTcon.glob=0; GBTcon.dist=0; GBTcon.local=0; GBTcon.other=0;
GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
for row = 1:rows(raw)
  case_id=raw(row,1); H=raw(row,2); B=raw(row,3); D=raw(row,4); t=raw(row,5);
  eta=raw(row,6); doverb=raw(row,7);
  kw_eq = 4 + 24*eta/(20 + 4.4*eta + eta^2);
  [prop,node,elem] = r04_make_channel_fm(H,B,D,t,E,nu,target);
  lengths = H*length_factors; m_all=cell(length(lengths),1);
  for ii=1:length(lengths); m_all{ii}=1; end
  [curve,~] = stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,1);
  first=zeros(length(curve),1);
  for ii=1:length(curve); first(ii)=curve{ii}(1,2); end
  [f_low,ix_low] = min(first);
  mins = [];
  for ii=2:(length(first)-1)
    if first(ii) <= first(ii-1) && first(ii) <= first(ii+1)
      xx=log(lengths(ii-1:ii+1)); yy=first(ii-1:ii+1); pp=polyfit(xx,yy,2);
      fref=first(ii); lref=lengths(ii);
      if pp(1)>0
        x0=-pp(2)/(2*pp(1));
        if x0>=xx(1) && x0<=xx(3); fref=polyval(pp,x0); lref=exp(x0); end
      end
      mins=[mins; lref, fref];
    end
  end
  if rows(mins)==0
    kw_first = f_low*12*(1-nu^2)*(H/t)^2/(pi^2*E);
    Lfirst = lengths(ix_low)/H;
    nmin = 0;
  else
    [~,i1] = min(mins(:,1));
    kw_first = mins(i1,2)*12*(1-nu^2)*(H/t)^2/(pi^2*E);
    Lfirst = mins(i1,1)/H;
    nmin = rows(mins);
  end
  kw_low = f_low*12*(1-nu^2)*(H/t)^2/(pi^2*E);
  fprintf(fid,'%d,%.6g,%.6g,%d,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,ok\n', ...
    case_id,eta,doverb,nmin,kw_low,lengths(ix_low)/H,kw_first,Lfirst,kw_eq,kw_low/kw_eq,kw_first/kw_eq);
  fflush(fid);
  fprintf('firstmin case=%d eta=%g nmin=%d ratio_low=%.4f ratio_first=%.4f Lfirst/H=%.3f\n', ...
    case_id,eta,nmin,kw_low/kw_eq,kw_first/kw_eq,Lfirst); fflush(stdout);
end
fclose(fid);
endfunction

function [prop,node,elem] = r04_make_channel_fm(H,B,D,t,E,nu,target)
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
