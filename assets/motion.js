(()=>{const calm=matchMedia('(prefers-reduced-motion: reduce)').matches;
const els=document.querySelectorAll('.reveal');
if(calm||!('IntersectionObserver'in window)){els.forEach(e=>e.classList.add('in'));return;}
document.documentElement.classList.add('motion');
const count=el=>{const to=+el.dataset.to,t0=performance.now(),d=900;const f=t=>{const k=Math.min(1,(t-t0)/d);el.textContent=Math.max(1,Math.round(to*(1-Math.pow(1-k,3))));if(k<1)requestAnimationFrame(f)};requestAnimationFrame(f)};
const io=new IntersectionObserver(es=>es.forEach(x=>{if(!x.isIntersecting)return;x.target.classList.add('in');x.target.querySelectorAll('.count').forEach(count);io.unobserve(x.target)}),{threshold:.15});
els.forEach(e=>io.observe(e));})();
