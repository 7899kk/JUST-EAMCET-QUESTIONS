import * as pdfjs from './vendor/pdf.min.mjs';
pdfjs.GlobalWorkerOptions.workerSrc=new URL('./vendor/pdf.worker.min.mjs',import.meta.url).href;
const docs=new Map(),pages=new Map();
const base=new URL('./vendor/',import.meta.url).href;
async function pageCanvas(path,n){
 const k=path+':'+n;if(pages.has(k))return pages.get(k);
 const promise=(async()=>{if(!docs.has(path))docs.set(path,pdfjs.getDocument({url:new URL(path,document.baseURI).href,cMapUrl:base+'cmaps/',cMapPacked:true,standardFontDataUrl:base+'standard_fonts/',wasmUrl:base+'wasm/'}).promise);const doc=await docs.get(path);const page=await doc.getPage(n),viewport=page.getViewport({scale:1.5}),canvas=document.createElement('canvas');canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);await page.render({canvasContext:canvas.getContext('2d'),viewport}).promise;return {canvas,scale:1.5};})();pages.set(k,promise);if(pages.size>8)pages.delete(pages.keys().next().value);return promise;
}
window.renderPDFRegions=async function(root){
 await Promise.all([...root.querySelectorAll('figure[data-pdf]')].map(async el=>{try{const {canvas,scale}=await pageCanvas(el.dataset.pdf,Number(el.dataset.page));if(!el.isConnected)return;const b=JSON.parse(el.dataset.bbox),crop=document.createElement('canvas');crop.width=Math.max(1,Math.ceil((b[2]-b[0])*scale));crop.height=Math.max(1,Math.ceil((b[3]-b[1])*scale));crop.getContext('2d').drawImage(canvas,b[0]*scale,b[1]*scale,crop.width,crop.height,0,0,crop.width,crop.height);crop.setAttribute('role','img');crop.setAttribute('aria-label',el.dataset.alt);crop.style.maxWidth='100%';crop.style.height='auto';el.replaceChildren(crop);}catch(e){el.textContent='Could not render this PDF region. Open the original PDF using the link below.';el.classList.add('error');}}));
};
window.dispatchEvent(new Event('pdfrendererready'));
