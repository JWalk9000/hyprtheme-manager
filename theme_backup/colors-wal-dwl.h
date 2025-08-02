/* Taken from https://github.com/djpohly/dwl/issues/466 */
#define COLOR(hex)    { ((hex >> 24) & 0xFF) / 255.0f, \
                        ((hex >> 16) & 0xFF) / 255.0f, \
                        ((hex >> 8) & 0xFF) / 255.0f, \
                        (hex & 0xFF) / 255.0f }

static const float rootcolor[]             = COLOR(0x0c141dff);
static uint32_t colors[][3]                = {
	/*               fg          bg          border    */
	[SchemeNorm] = { 0xc2c4c6ff, 0x0c141dff, 0x5c6570ff },
	[SchemeSel]  = { 0xc2c4c6ff, 0x8A7767ff, 0x857B2Dff },
	[SchemeUrg]  = { 0xc2c4c6ff, 0x857B2Dff, 0x8A7767ff },
};
