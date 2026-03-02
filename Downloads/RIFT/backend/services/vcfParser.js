const fs = require('fs');

/**
 * Parse VCF file and extract variant information.
 * @param {string} filePath - Path to uploaded VCF file.
 * @returns {Array} Array of variants with rsid, chromosome, position, etc.
 */
function parseVCF(filePath) {
  const data = fs.readFileSync(filePath, 'utf8');
  const lines = data.split('\n');
  const variants = [];

  for (const line of lines) {
    if (line.startsWith('#')) continue; // skip headers
    if (!line.trim()) continue;

    const parts = line.split('\t');
    if (parts.length < 8) continue;

    const chrom = parts[0];
    const pos = parts[1];
    const id = parts[2]; // rsID or other identifier
    const ref = parts[3];
    const alt = parts[4];
    const info = parts[7];

    // Extract rsID if present (could be multiple, take first)
    let rsid = id;
    if (id === '.' || !id.startsWith('rs')) {
      // Try to extract from INFO field
      const rsMatch = info.match(/RS=(\d+)/);
      rsid = rsMatch ? `rs${rsMatch[1]}` : null;
    }

    if (rsid && rsid.startsWith('rs')) {
      variants.push({
        rsid,
        chrom,
        pos,
        ref,
        alt,
        info,
      });
    }
  }

  return variants;
}

module.exports = parseVCF;