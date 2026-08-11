import {readPdf,renderPage} from './pdf-engine.js';
import {ocrCanvas} from './ocr-engine.js';
import {buildLines,buildParagraphs,normalizeText} from './layout-engine.js';
import {detectTables} from './table-engine.js';
import {downloadDocx} from './docx-engine.js';
import {API_BASE_URL} from './config.js';

const $=id=>document.getElementById(id);
let file=null;
$('fileInput').addEventListener('change',e=>setFile(e.target.files[0]));
$('dropZone').addEventListener('dragover',e=>e.preventDefault());
$('dropZone').addEventListener('drop',e=>{e.preventDefault();setFile(e.dataTransfer.files[0])});
function setFile(f){if(!f)return;if(!/^(application\/pdf|image\/png|image\/jpeg)$/.test(f.type)){setStatus('فرمت پشتیبانی نمی‌شود.');return}file=f;$('fileName').textContent=f.name;$('convertBtn').disabled=false;setStatus('فایل آماده است.')}
function setStatus(s){$('status').textContent=s}
function progress(v){$('progressBar').style.width=Math.max(0,Math.min(100,v))+'%'}
async function imageFileToCanvas(f){const url=URL.createObjectURL(f);const img=await new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=rej;i.src=url});const c=document.createElement('canvas');const scale=Math.min(2.4,2800/Math.max(img.width,img.height));c.width=Math.round(img.width*scale);c.height=Math.round(img.height*scale);c.getContext('2d').drawImage(img,0,0,c.width,c.height);URL.revokeObjectURL(url);return c}
async function backendConvert(){const qs=new URLSearchParams({ocr_mode:$('ocrMode').value,language:$('ocrLang').value,table_mode:$('tableMode').value});const r=await fetch(`${API_BASE_URL.replace(/\/$/,'')}/convert?${qs}`,{method:'POST',body:(()=>{const f=new FormData();f.append('file',file,file.name);return f})()});if(!r.ok)throw new Error((await r.text())||`Backend HTTP ${r.status}`);const blob=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=file.name.replace(/\.[^.]+$/,'')+'.docx';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);return true}

$('convertBtn').addEventListener('click',async()=>{if(!file)return;try{$('convertBtn').disabled=true;progress(2);
  if(API_BASE_URL){setStatus('در حال تبدیل با Backend حرفه‌ای…');await backendConvert();progress(100);setStatus('✓ DOCX از Backend ساخته و دانلود شد.');return}
  const model={pages:[]};let totalWords=0,ocrPages=0,tables=0,conf=[];
  if(file.type==='application/pdf'){
    const pages=await readPdf(file,(n,total)=>{setStatus(`استخراج صفحه ${n} از ${total}…`);progress(5+n/total*25)});$('pages').textContent=pages.length;
    for(let i=0;i<pages.length;i++){const p=pages[i];let words=p.spans.map(s=>({...s,text:normalizeText(s.text),confidence:100,fontFamily:s.fontName,fontSize:s.fontSize}));let usedOCR=false;
      if($('ocrMode').value==='always'||($('ocrMode').value==='auto'&&words.length<4)){setStatus(`OCR صفحه ${i+1}…`);const c=await renderPage(file,i+1,2.4);const r=await ocrCanvas(c,$('ocrLang').value,x=>progress(30+(i+(x||0))/pages.length*45));words=r.words;conf.push(r.confidence);usedOCR=true;ocrPages++}else conf.push(100);
      const lines=buildLines(words);const paragraphs=buildParagraphs(lines);const ts=detectTables(lines,$('tableMode').value);tables+=ts.length;const blocks=[];for(const t of ts)blocks.push({type:'table',rows:t.rows});if(!ts.length)for(const pa of paragraphs)blocks.push({type:'paragraph',rtl:pa.rtl,lines:pa.lines});model.pages.push({number:p.number,blocks,usedOCR});totalWords+=words.length;$('words').textContent=totalWords;$('ocrPages').textContent=ocrPages;$('tables').textContent=tables;progress(30+(i+1)/pages.length*65)}
  }else{const c=await imageFileToCanvas(file);$('pages').textContent='1';setStatus('OCR تصویر…');const r=await ocrCanvas(c,$('ocrLang').value,x=>progress(5+(x||0)*70));const lines=buildLines(r.words);const paragraphs=buildParagraphs(lines);const ts=detectTables(lines,$('tableMode').value);model.pages.push({number:1,blocks:ts.length?ts.map(t=>({type:'table',rows:t.rows})):paragraphs.map(pa=>({type:'paragraph',rtl:pa.rtl,lines:pa.lines})),usedOCR:true});totalWords=r.words.length;ocrPages=1;tables=ts.length;conf=[r.confidence];$('words').textContent=totalWords;$('ocrPages').textContent=1;$('tables').textContent=tables}
  $('confidence').textContent=(conf.reduce((a,b)=>a+b,0)/Math.max(1,conf.length)).toFixed(0)+'%';$('structure').textContent=`صفحات: ${model.pages.length}\nبلوک‌های متن: ${model.pages.reduce((a,p)=>a+p.blocks.filter(b=>b.type==='paragraph').length,0)}\nجدول‌ها: ${tables}\nصفحات OCR: ${ocrPages}\nمیانگین اعتماد OCR: ${$('confidence').textContent}`;setStatus('بازسازی تمام شد؛ DOCX در حال ساخته‌شدن است…');await downloadDocx(model,file.name);progress(100);setStatus('✓ DOCX واقعی ساخته و دانلود شد.')
}catch(e){console.error(e);setStatus('خطا: '+(e.message||e))}finally{$('convertBtn').disabled=false}});
if('serviceWorker'in navigator)navigator.serviceWorker.register('./sw.js').catch(()=>{});
