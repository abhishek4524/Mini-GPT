const mongoose = require('mongoose');

const variantSchema = new mongoose.Schema({
  rsid: { type: String, required: true, unique: true },
  gene: { type: String, required: true },
  star: { type: String, required: true },          // e.g., "*1", "*2"
  impact: { type: String },                         // e.g., "missense"
  function: { type: String },                        // e.g., "normal function", "decreased function"
});

module.exports = mongoose.model('Variant', variantSchema);