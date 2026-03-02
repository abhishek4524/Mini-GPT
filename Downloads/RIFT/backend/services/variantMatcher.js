const Variant = require('../models/Variant');

/**
 * Match parsed variants against database and return gene/star allele info.
 * @param {Array} variants - Array from vcfParser.
 * @returns {Array} Array of matched variants with gene and star allele.
 */
async function matchVariants(variants) {
  const rsids = variants.map(v => v.rsid);
  const matched = await Variant.find({ rsid: { $in: rsids } });

  // Map back to original variants
  return variants.map(vcfVar => {
    const dbMatch = matched.find(m => m.rsid === vcfVar.rsid);
    if (dbMatch) {
      return {
        ...vcfVar,
        gene: dbMatch.gene,
        star: dbMatch.star,
        impact: dbMatch.impact,
        function: dbMatch.function,
      };
    }
    return {
      ...vcfVar,
      gene: null,
      star: null,
      impact: null,
      function: null,
    };
  }).filter(v => v.gene); // only keep known variants
}

module.exports = matchVariants;