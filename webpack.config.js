const webpack = require('webpack');
const path = require('path');

const PATHS = {
  dev: path.join(__dirname, './www/static/dev'),
  build: path.join(__dirname, './www/static/build')
};

module.exports = {
  entry: {
    index: path.join(PATHS.dev, 'index')
  },
  output: {
    path: PATHS.build,
    filename: "[name].entry.js"
  },
  module: {
    loaders: [
    {
      test: /\.css$/,
      loaders: ['style', 'css'],
      include: PATHS.dev
    },
    {
      test: /\.js$/,
      loader: 'babel',
      include: PATHS.dev
    }
    ]
  },
  devtool: 'eval-source-map',
  devServer: {
    contentBase: PATHS.build,
    hot: true,
    inline: true
  },
  plugins: [
    new webpack.HotModuleReplacementPlugin()
  ]
}
