function r05_expand_runs(mode)
% Dispatcher so Octave can see this file by its filename.
if strcmp(mode,'round')
  r05_round_corner_run();
elseif strcmp(mode,'bend')
  r05_bending_run();
else
  error('mode must be round or bend');
end
endfunction

function r05_round_corner_run()
% R05: same 15 lipped-channel sections as the sharp-corner RP23-01 sample,
% with centreline corner radius r = 2.5 t. Flat lengths h, b, d are unchanged.
% Signature-curve minimum on 0.25h..2.0h. RP23-01 Section 3 uses round corners
% with at least four elements; this run uses six segments per quarter-circle.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/analysis/cFSM']);
addpath([repo '/cutwp']); addpath([repo '/helpers']); addpath([repo '/interface']);
addpath([repo '/plotters']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
warning('off','all');
raw = dlmread([root '/external_sources/rp23001_rebuild/rp23001_cases_numeric.csv'], ',', 1, 0);
fid = fopen([root '/outputs/r05_rp2301_round_corner.csv'],'w');
fprintf(fid,'case_id,eta_w,D_over_B,r_over_t,kw_fsm,kw_equation19,ratio,L_over_H,nodes,status\n');
E=203000; nu=0.30; t=1.0; r=2.5; target=3.0; nlengths=36;
fac=logspace(log10(0.25),log10(2.0),nlengths)';
springs=0; constraints=0; BC='S-S';
GBTcon.glob=0; GBTcon.dist=0; GBTcon.local=0; GBTcon.other=0;
GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
for row=1:rows(raw)
  H=raw(row,2); B=raw(row,3); D=raw(row,4); eta=raw(row,6); doverb=raw(row,7);
  if r>=D || r>=B/2
    fprintf(fid,'%d,%.6g,%.6g,%.3g,nan,nan,nan,nan,0,skipped_radius\n', raw(row,1),eta,doverb,r/t);
    fflush(fid); continue;
  end
  kw_eq = 4 + 24*eta/(20 + 4.4*eta + eta^2);
  [prop,node,elem] = r05_channel(H,B,D,t,r,E,nu,target);
  lengths=H*fac; m_all=cell(length(lengths),1);
  for ii=1:length(lengths); m_all{ii}=1; end
  [curve,~]=stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,1);
  first=zeros(length(curve),1);
  for ii=1:length(curve); first(ii)=curve{ii}(1,2); end
  [fcrl,ix]=min(first);
  if ix>1 && ix<length(first)
    xx=log(lengths(ix-1:ix+1)); yy=first(ix-1:ix+1); pp=polyfit(xx,yy,2);
    if pp(1)>0
      x0=-pp(2)/(2*pp(1));
      if x0>=xx(1) && x0<=xx(3); fcrl=polyval(pp,x0); end
    end
  end
  kw=fcrl*12*(1-nu^2)*(H/t)^2/(pi^2*E);
  fprintf(fid,'%d,%.6g,%.6g,%.3g,%.6g,%.6g,%.6g,%.6g,%d,ok\n', raw(row,1),eta,doverb,r/t,kw,kw_eq,kw/kw_eq,lengths(ix)/H,rows(node));
  fflush(fid);
  fprintf('round case=%d eta=%g ratio=%.4f\n', raw(row,1), eta, kw/kw_eq); fflush(stdout);
end
fclose(fid);
endfunction

function r05_bending_run()
% R05: major-axis bending branch of AISI RP23-01 Eqs. (20)-(23), sharp-corner
% centreline channels. Stress varies linearly with the web coordinate about
% mid-height. Flange branch (eta<2.57) is compared through (t/b); web branch
% through (t/h). Not the report's round-corner library.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/analysis/cFSM']);
addpath([repo '/cutwp']); addpath([repo '/helpers']); addpath([repo '/interface']);
addpath([repo '/plotters']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
warning('off','all');
fid = fopen([root '/outputs/r05_rp2301_bending.csv'],'w');
fprintf(fid,'case_id,eta_w,D_over_B,branch,k_fsm,k_equation,ratio,L_over_H,status\n');
E=203000; nu=0.30; t=1.0; H=200; target=3.0; nlengths=36;
etas=[1.5, 2.2, 4.472136, 8, 12, 16];
dob=0.25;
fac=logspace(log10(0.25),log10(2.0),nlengths)';
springs=0; constraints=0; BC='S-S';
GBTcon.glob=0; GBTcon.dist=0; GBTcon.local=0; GBTcon.other=0;
GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
cid=0;
for eta=etas
  cid=cid+1; B=H/eta; D=dob*B;
  if eta<2.57
    branch='flange';
    k_eq=(4.93 - 3.15*eta + 0.53*eta^2)/(1 - 0.64*eta + 0.11*eta^2);
    width=B;
  else
    branch='web';
    k_eq=(-4.3*eta + 6.44*eta^2)/(1 - 0.54*eta + 0.24*eta^2);
    width=H;
  end
  [prop,node,elem]=r05_channel(H,B,D,t,0,E,nu,target);
  y=node(:,3); ymid=0.5*(max(y)+min(y));
  node(:,8)=(y-ymid)/(max(y)-ymid);
  lengths=H*fac; m_all=cell(length(lengths),1);
  for ii=1:length(lengths); m_all{ii}=1; end
  [curve,~]=stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,1);
  first=zeros(length(curve),1);
  for ii=1:length(curve); first(ii)=curve{ii}(1,2); end
  [fcrl,ix]=min(first);
  if ix>1 && ix<length(first)
    xx=log(lengths(ix-1:ix+1)); yy=first(ix-1:ix+1); pp=polyfit(xx,yy,2);
    if pp(1)>0
      x0=-pp(2)/(2*pp(1));
      if x0>=xx(1) && x0<=xx(3); fcrl=polyval(pp,x0); end
    end
  end
  k_fsm=fcrl*12*(1-nu^2)*(width/t)^2/(pi^2*E);
  fprintf(fid,'%d,%.6g,%.3g,%s,%.6g,%.6g,%.6g,%.6g,ok\n', cid,eta,dob,branch,k_fsm,k_eq,k_fsm/k_eq,lengths(ix)/H);
  fflush(fid);
  fprintf('bend eta=%g branch=%s ratio=%.4f k_fsm=%.3f k_eq=%.3f\n', eta, branch, k_fsm/k_eq, k_fsm, k_eq); fflush(stdout);
end
fclose(fid);
endfunction

function [prop,node,elem]=r05_channel(H,B,D,t,r,E,nu,target)
  if r<=0
    P=[B, H-D; B, H; 0, H; 0, 0; B, 0; B, D];
  else
    n=6;
    P=[B+2*r, H+r-D];
    P=[P; B+2*r, H+r];
    P=[P; r05_arc(B+r, H+r, r, 0, pi/2, n)];
    P=[P; r, H+2*r];
    P=[P; r05_arc(r, H+r, r, pi/2, pi, n)];
    P=[P; 0, r];
    P=[P; r05_arc(r, r, r, pi, 3*pi/2, n)];
    P=[P; B+r, 0];
    P=[P; r05_arc(B+r, r, r, 3*pi/2, 2*pi, n)];
    P=[P; B+2*r, r+D];
  end
  coords=[];
  for s=1:(rows(P)-1)
    p0=P(s,:); p1=P(s+1,:);
    if norm(p1-p0)<1e-9; continue; end
    nseg=max(1,ceil(norm(p1-p0)/target));
    for j=0:(nseg-1); coords=[coords; p0+(p1-p0)*(j/nseg)]; end
  end
  coords=[coords; P(end,:)];
  nn=rows(coords);
  node=[(1:nn)' coords ones(nn,4)]; node(:,8)=1;
  elem=[(1:(nn-1))' (1:(nn-1))' (2:nn)' repmat(t,nn-1,1) repmat(100,nn-1,1)];
  prop=[100 E E nu nu E/(2*(1+nu))];
endfunction

function A=r05_arc(cx,cy,r,a0,a1,n)
  ang=linspace(a0,a1,n+1)';
  A=[cx+r*cos(ang), cy+r*sin(ang)];
  A=A(2:end-1,:);
endfunction
