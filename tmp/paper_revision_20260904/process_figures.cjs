const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const sharp = require('sharp');

const root = path.resolve(__dirname, '../..');
const dest = path.join(root, '论文图片/方法框架/20260904');
const source = 'C:/Users/TOP令隹/AppData/Local/Temp';
// Coordinates refer to the unchanged original image; rectangles are half-open.
// Masks cover prose only, keeping box borders, arrows, labels and formulas intact.
const specs = [
  {name: '图1_总体框架', input: 'codex-clipboard-a78c1a0f-f0d7-4972-9c27-0c730e232675.png', masks: []},
  {name: '图2_状态引导', input: 'codex-clipboard-c95fc51f-1c29-4d1b-b74c-b4829fb2f6f4.png', masks: [
    {box: [249, 415, 449, 441], color: [255,255,255,255]},
    {box: [485, 366, 683, 389], color: [255,255,255,255]},
  ]},
  {name: '图3_状态智能体', input: 'codex-clipboard-430b0516-0328-4879-ad4b-ac682516e285.png', masks: []},
  {name: '图4_知识智能体', input: 'codex-clipboard-18eac622-ea12-4b31-8281-87bf935418d7.png', masks: [
    {box: [239, 358, 335, 389], sampleX: 280, sampleY: 390},
    {box: [398, 358, 502, 389], sampleX: 440, sampleY: 390},
    {box: [563, 358, 668, 389], sampleX: 610, sampleY: 390},
    {box: [735, 358, 833, 389], sampleX: 780, sampleY: 390},
  ]},
  {name: '图5_生成智能体', input: 'codex-clipboard-5032a236-d5d9-4fcd-9b51-e47aa1e2a54f.png', masks: [
    {box: [308, 408, 444, 442], color: [255,255,255,255]},
  ]},
];

(async () => {
  const results = [];
  for (const spec of specs) {
    const input = path.join(source, spec.input);
    const inputHash = crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex');
    const {data: original, info} = await sharp(input).ensureAlpha().raw().toBuffer({resolveWithObject: true});
    const edited = Buffer.from(original);
    const [left, top, right, bottom] = spec.crop || [0, 0, info.width, info.height];
    if (left < 0 || top < 0 || right > info.width || bottom > info.height) throw Error('Invalid crop');
    for (const mask of spec.masks) {
      const [x1, y1, x2, y2] = mask.box;
      for (let y=y1; y<y2; y++) {
        const bg=((mask.sampleY ?? y)*info.width+(mask.sampleX || 0))*4;
        for (let x=x1; x<x2; x++) {
          if(mask.color) for(let c=0;c<4;c++) edited[(y*info.width+x)*4+c]=mask.color[c];
          else original.copy(edited,(y*info.width+x)*4,bg,bg+4);
        }
      }
    }
    const output=path.join(dest, `${spec.name}.png`);
    await sharp(edited,{raw:{width:info.width,height:info.height,channels:4}})
      .extract({left,top,width:right-left,height:bottom-top}).png().toFile(output);
    const decoded=await sharp(output).ensureAlpha().raw().toBuffer();
    let changedOutsideMasks=0, changedInsideMasks=0;
    for(let y=top;y<bottom;y++) for(let x=left;x<right;x++) {
      const src=(y*info.width+x)*4, dst=((y-top)*(right-left)+x-left)*4;
      const differs=[0,1,2,3].some(c=>original[src+c]!==decoded[dst+c]);
      if (!differs) continue;
      const allowed=spec.masks.some(m=>x>=m.box[0]&&x<m.box[2]&&y>=m.box[1]&&y<m.box[3]);
      if(allowed) changedInsideMasks++; else changedOutsideMasks++;
    }
    if(changedOutsideMasks) throw Error(`Unexpected pixel modifications: ${spec.name}`);
    const afterHash=crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex');
    if(afterHash!==inputHash) throw Error('Original file modified');
    results.push({...spec,width:right-left,height:bottom-top,sourceHash:inputHash,changedInsideMasks,changedOutsideMasks,originalUnchanged:true});
  }
  fs.writeFileSync(path.join(__dirname,'figure_pixel_audit.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
