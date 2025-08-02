const char *colorname[] = {

  /* 8 normal colors */
  [0] = "#0c141d", /* black   */
  [1] = "#857B2D", /* red     */
  [2] = "#8A7767", /* green   */
  [3] = "#958F38", /* yellow  */
  [4] = "#9F8A77", /* blue    */
  [5] = "#738484", /* magenta */
  [6] = "#AF9985", /* cyan    */
  [7] = "#c2c4c6", /* white   */

  /* 8 bright colors */
  [8]  = "#5c6570",  /* black   */
  [9]  = "#857B2D",  /* red     */
  [10] = "#8A7767", /* green   */
  [11] = "#958F38", /* yellow  */
  [12] = "#9F8A77", /* blue    */
  [13] = "#738484", /* magenta */
  [14] = "#AF9985", /* cyan    */
  [15] = "#c2c4c6", /* white   */

  /* special colors */
  [256] = "#0c141d", /* background */
  [257] = "#c2c4c6", /* foreground */
  [258] = "#c2c4c6",     /* cursor */
};

/* Default colors (colorname index)
 * foreground, background, cursor */
 unsigned int defaultbg = 0;
 unsigned int defaultfg = 257;
 unsigned int defaultcs = 258;
 unsigned int defaultrcs= 258;
