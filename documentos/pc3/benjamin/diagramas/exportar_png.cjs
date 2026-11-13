/* Exportación local reproducible. Resuelva SHARP_PATH al módulo sharp del runtime. */
const fs = require('node:fs');
const path = require('node:path');
const sharp = require(process.env.SHARP_PATH || 'sharp');
async function main() {
  for (const file of fs.readdirSync(__dirname).filter(x => x.endsWith('.svg'))) {
    const input = path.join(__dirname, file);
    await sharp(input, {density: 180}).png().toFile(input.replace(/\.svg$/, '.png'));
    process.stdout.write(file + ' → PNG\n');
  }
}
main().catch(e => { process.stderr.write(String(e)); process.exitCode = 1; });
