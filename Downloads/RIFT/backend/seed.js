require('dotenv').config();
const connectDB = require('./config/db');
const Variant = require('./models/Variant');
const seedData = require('./data/variantSeed.json');

const seedDB = async () => {
  try {
    await connectDB();
    await Variant.deleteMany({});
    await Variant.insertMany(seedData);
    console.log('Database seeded successfully');
    process.exit(0);
  } catch (err) {
    console.error('Seeding error:', err);
    process.exit(1);
  }
};

seedDB();