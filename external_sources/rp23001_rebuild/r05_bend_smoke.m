function r05_bend_smoke()
% One-section check: major-axis bending must use the smallest positive
% eigenvalue. A single-eigenvalue call returns a near-zero root when the
% geometric stiffness is indefinite.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
repo = [root '/external_sources/cufsm-git'];
addpath(repo); addpath([repo '/analysis']); addpath([repo '/cutwp']);
addpath([repo '/helpers']); addpath([root '/external_sources/cufsm_octave_compat/analysis']);
warning('off','all');
H=200; eta=4.472136; B=H/eta; D=0.25*B; t=1; E=203000; nu=0.30;
[prop,node,elem] = r05_smoke_channel(H,B,D,t,E,nu,4);
y=node(:,3); ymid=0.5*(max(y)+min(y));
node(:,8)=(y-ymid)/max(abs(y-ymid));
fprintf('stress range %.3f %.3f\n', min(node(:,8)), max(node(:,8)));
lengths = H*logspace(log10(0.4), log10(1.6), 5)';
m_all=cell(5,1); for i=1:5; m_all{i}=1; end
springs=0; constraints=0; BC='S-S';
GBTcon.glob=0; GBTcon.dist=0; GBTcon.local=0; GBTcon.other=0;
GBTcon.ospace=1; GBTcon.couple=1; GBTcon.orth=2; GBTcon.norm=1;
[curve,~]=stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,6);
for i=1:5
  vals=sort(curve{i}(:,2));
  pos=vals(vals>0);
  fprintf('L/H=%.3f eigs=%s  first_pos=%.4f\n', lengths(i)/H, sprintf(' %.3f', vals'), pos(1));
end
k_eq=(-4.3*eta + 6.44*eta^2)/(1 - 0.54*eta + 0.24*eta^2);
fprintf('k_eq web branch %.3f\n', k_eq);
endfunction

function [prop,node,elem]=r05_smoke_channel(H,B,D,t,E,nu,target)
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
