const openai = require('../config/openai');

async function generateExplanation(data) {
  const prompt = `You are a pharmacogenomics expert. Given the following analysis, write a concise patient-friendly explanation.

Drug: ${data.drug}
Gene: ${data.gene}
Diplotype: ${data.diplotype}
Phenotype: ${data.phenotype}
Risk: ${data.risk}
Variants: ${JSON.stringify(data.variants)}
Recommendation: ${JSON.stringify(data.recommendation)}

Write a paragraph explaining the result and its implications for the patient.`;

  try {
    const response = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'llama-3.3-70b-versatile',
      messages: [
        { role: 'system', content: 'You are a helpful pharmacogenomics assistant.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.3,
      max_tokens: 300,
    });

    return response.choices[0].message.content.trim();
  } catch (err) {
    console.error('LLM error:', err);
    return 'AI explanation temporarily unavailable. Please refer to the CPIC recommendation above.';
  }
}

module.exports = { generateExplanation };