/**
 * Calculate confidence score based on evidence level.
 * @param {Array} variants - Matched variants with known function.
 * @param {boolean} isKnownCpic - Whether the drug-gene pair has CPIC guidelines.
 * @returns {number} Confidence score between 0 and 1.
 */
function computeConfidenceScore(variants, isKnownCpic) {
  if (!variants || variants.length === 0) return 0.0;

  // Count how many variants have known function
  const knownFunctions = variants.filter(v => v.function && v.function !== 'unknown').length;
  const ratio = knownFunctions / variants.length;

  if (isKnownCpic && ratio > 0.8) return 0.95;
  if (isKnownCpic && ratio > 0.5) return 0.8;
  if (!isKnownCpic && ratio > 0.5) return 0.7;
  return 0.4;
}

module.exports = { computeConfidenceScore };