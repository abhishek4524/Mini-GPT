/**
 * Determine phenotype based on gene and star allele combination.
 * For simplicity, we assume each gene has its own logic.
 * This is a mock implementation; in reality you'd query a CPIC database.
 */
function getPhenotype(gene, diplotype) {
  // diplotype example: "*1/*2"
  const alleles = diplotype.split('/').map(a => a.replace('*', ''));
  if (gene === 'CYP2D6') {
    // simplified logic
    if (alleles.includes('4') || alleles.includes('5')) return 'Poor Metabolizer';
    if (alleles.includes('10') || alleles.includes('17')) return 'Intermediate Metabolizer';
    if (alleles.includes('1') || alleles.includes('2')) return 'Normal Metabolizer';
    if (alleles.includes('xn')) return 'Ultrarapid Metabolizer';
    return 'Indeterminate';
  }
  if (gene === 'CYP2C9') {
    if (alleles.includes('3') && alleles.includes('3')) return 'Poor Metabolizer';
    if (alleles.includes('2') || alleles.includes('3')) return 'Intermediate Metabolizer';
    return 'Normal Metabolizer';
  }
  if (gene === 'VKORC1') {
    if (alleles.includes('2') && alleles.includes('2')) return 'Low sensitivity';
    if (alleles.includes('2')) return 'Intermediate sensitivity';
    return 'Normal sensitivity';
  }
  return 'Unknown';
}

module.exports = { getPhenotype };