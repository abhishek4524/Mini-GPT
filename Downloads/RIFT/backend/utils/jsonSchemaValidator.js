const Ajv = require('ajv');
const ajv = new Ajv();

// Define the expected JSON schema for the final response
const responseSchema = {
  type: 'object',
  properties: {
    drug: { type: 'string' },
    gene: { type: 'string' },
    diplotype: { type: 'string' },
    phenotype: { type: 'string' },
    risk: { type: 'string' },
    variants: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          rsid: { type: 'string' },
          gene: { type: 'string' },
          star: { type: 'string' },
          impact: { type: 'string' },
          function: { type: 'string' },
        },
        required: ['rsid', 'gene', 'star'],
      },
    },
    recommendation: {
      type: 'object',
      properties: {
        dosageAdjustment: { type: 'string' },
        alternativeDrugs: { type: 'array', items: { type: 'string' } },
        monitoring: { type: 'string' },
      },
      required: ['dosageAdjustment', 'monitoring'],
    },
    explanation: { type: 'string' },
    confidenceScore: { type: 'number' },
  },
  required: ['drug', 'gene', 'diplotype', 'phenotype', 'risk', 'variants', 'recommendation', 'explanation', 'confidenceScore'],
};

const validate = ajv.compile(responseSchema);

function validateResponse(data) {
  const valid = validate(data);
  if (!valid) {
    throw new Error(`Schema validation failed: ${JSON.stringify(validate.errors)}`);
  }
  return true;
}

module.exports = { validateResponse };