const express = require('express');
const multer = require('multer');
const { analyze } = require('../controllers/analyzeController');

const router = express.Router();

// Configure multer for in-memory storage (or disk)
const upload = multer({ dest: 'uploads/' }); // files saved to /uploads temporarily

router.post('/analyze', upload.single('vcf_file'), analyze);

module.exports = router;