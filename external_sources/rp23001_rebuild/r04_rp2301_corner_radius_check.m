function r04_rp2301_corner_radius_check()
% R04 W2 corner-radius sensitivity: the RP23-01 report models round corners
% ("at least 4 elements"), while the main independent rebuild used a sharp-corner
% centreline polyline. This check rebuilds the high-eta cases with rounded corners
% (inserted fillet arcs at centreline radius rc) to test whether the 13-15% deviation
% at the domain corner is driven by corner modelling.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/analysis/cFSM']);
addpath([repo '/cutwp']); addpath([repo '/helpers']); addpath([repo '/interface']);
addpath([repo '/plotters']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
E = 203000; nu = 0.30; t = 1.0;
out_file = [root '/outputs/r04_rp2301_corner_radius_check.csv'];
fid = fopen(out_file,'w');
fprintf(fid,'eta,D_over_B,rc_over_t,kw_fsm,kw_equation19,ratio\n');
springs=0; constraints=0; BC='S-S';
GBTcon.glob=0; GBTcon.dist=0; GBTcon.local=0; GBTcon.other=0; GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
cases = {250, 250/12, 0.25*250/12, 12.0;
         250, 250/20, 0.40*250/20, 20.0};
for c = 1:rows(cases)
  H = cases{c,1}; B = cases{c,2}; D = cases{c,3}; eta = cases{c,4};
  kw_eq = 4 + 24*eta/(20 + 4.4*eta + eta^2);
  for rc_t = [0.0, 2.5, 5.0]   # sharp, rc=2.5t, rc=5t
    [prop,node,elem] = r04_make_channel_round(H,B,D,t,E,nu,1.5,rc_t*t);
    if rc_t == 0.0
      % sharp-corner model identical to the main rebuild (sanity row)
      [prop,node,elem] = r04_make_channel(H,B,D,t,E,nu,1.5);
    end
    length_factors = logspace(log10(0.10), log10(4.0), 64)';
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
    fprintf(fid,'%.6g,%.6g,%.3g,%.6g,%.6g,%.6g\n', eta, D/B, rc_t, kw_fsm, kw_eq, ratio);
    fprintf('eta=%g rc/t=%g kw_fsm=%.4f ratio=%.4f nodes=%d\n', eta, rc_t, kw_fsm, ratio, rows(node)); fflush(stdout);
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

function [prop,node,elem] = r04_make_channel_round(H,B,D,t,E,nu,target,rc)
% Rounded-corner centreline path: upper lip tip -> arc(flangelip) -> upper flange ->
% arc(webflange) -> web -> arc(webflange) -> lower flange -> arc(flangelip) -> lower lip tip.
% Flat segments keep the outer centreline dims; fillet arcs of centreline radius rc
% (approximated by 5 segments each) are inserted at the four corners.
  if rc <= 0; rc = 1e-12; end
  nseg = 5;
  pts = [];
  % upper lip tip
  pts = [pts; B, H-D];
  % corner: upper flange - upper lip, centre (B-rc, H-rc): from (B, H-rc) to (B-rc, H)
  pts = [pts; arc_pts(B-rc, H-rc, rc, 0, pi/2, nseg, false)];
  % upper flange to corner: upper flange - web, centre (rc, H-rc): from (rc, H) to (0, H-rc)
  pts = [pts; arc_pts(rc, H-rc, rc, pi/2, pi, nseg, false)];
  % web to corner: web - lower flange, centre (rc, rc): from (0, rc) to (rc, 0)
  pts = [pts; arc_pts(rc, rc, rc, pi, 3*pi/2, nseg, false)];
  % lower flange to corner: lower flange - lower lip, centre (B-rc, rc): from (B-rc, 0) to (B, rc)
  pts = [pts; arc_pts(B-rc, rc, rc, 3*pi/2, 2*pi, nseg, false)];
  % lower lip tip
  pts = [pts; B, D];
  % polyline discretisation
  coords=[];
  for s=1:(rows(pts)-1)
    p0=pts(s,:); p1=pts(s+1,:); n=max(1,ceil(norm(p1-p0)/target));
    for j=0:(n-1); coords=[coords; p0+(p1-p0)*(j/n)]; end
  end
  coords=[coords; pts(end,:)]; nn=rows(coords);
  node=[(1:nn)' coords ones(nn,4)]; node(:,8)=1;
  elem=[(1:(nn-1))' (1:(nn-1))' (2:nn)' repmat(t,nn-1,1) repmat(100,nn-1,1)];
  prop=[100 E E nu nu E/(2*(1+nu))];
endfunction

function A = arc_pts(cx, cy, r, a0, a1, nseg, reverse)
  ang = linspace(a0, a1, nseg+1)';
  A = [cx + r*cos(ang), cy + r*sin(ang)];
  A = A(1:end-1,:);
endfunction