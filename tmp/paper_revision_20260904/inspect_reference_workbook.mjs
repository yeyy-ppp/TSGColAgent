import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const source = 'D:/wn/Visio_Editable_10_Figures_Full_Package/reference_png/多智能体论文方法数据.xlsx';
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(source));
const result = await workbook.inspect({kind:'sheet',include:'id,name',maxChars:2000});
console.log(result.ndjson);
const previews=[['dataset','AC21:AK29'],['execution','AN86:AW100'],['state_quality','AM113:AU130'],['scheduling','AM133:AU150'],['knowledge','AM152:AU165'],['last_tables','AC151:AG157']];
for(const [name,range] of previews){
  const blob=await workbook.render({sheetName:'Sheet1',range,scale:1,format:'png'});
  const destination=path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(?=[A-Za-z]:)/,'')),`reference_${name}.png`);
  await fs.writeFile(decodeURI(destination),new Uint8Array(await blob.arrayBuffer()));
  console.log(decodeURI(destination));
}
