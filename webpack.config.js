const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  mode: 'production',
  entry: './apps/static/js/index',
  output: {
    path: path.resolve('./apps/static/js/'),
    filename: "[name].js"
  },
  devtool: 'source-map',
  plugins: [
    new BundleTracker({filename: './webpack-stats.json'})
  ],
  module: {
    rules: [
      {
        test: /\.js$/,
        enforce: 'pre',
        use: ['source-map-loader'],
      },
    ],
  }
}