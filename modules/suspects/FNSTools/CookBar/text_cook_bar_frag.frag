// by hexagons
// 181202

out vec4 frag;

uniform vec4 transInfo[250];
uniform vec2 extraInfo[250];
uniform vec4 cookInfo[250];
uniform vec2 gpuMem[250];

uniform float zoom;
uniform int edge;
uniform vec4 bgColor;
uniform int absTime;
uniform int count;
uniform bool nonCommercial;

vec4 matte(vec4 forground, vec4 background, float opacity) {
	vec3 rgb = forground.rgb * opacity + background.rgb * (1.0 - opacity);
	vec4 rgba = vec4(rgb, 1.0);
	return rgba;
}

vec4 brightness(vec4 color, float brightness) {
	vec3 rgb = color.rgb * brightness;
	vec4 rgba = vec4(rgb, color.a);
	return rgba;
}

void main() {

	vec4 res = uTDOutputInfo.res;
	int x = int(round(vUV.s * res[2] - 0.5));
	int y = int(round(vUV.t * res[3] - 0.5));
	if (nonCommercial) {
		x *= 2;
		y *= 2;
	}

	bool insideBar = false;
	bool insideLevel = false;
	bool insideStripe = false;

	bool cooking = false;
	float cookLevel = 0;
	
	float opacity = 0.0;

	bool isMem = false;

	// Scan through all OPs
	for (int i = 0; i < count; i++) {

		// op trans
		float opOriginX = transInfo[i][0];
		float opOriginY = transInfo[i][1];
		float opWidth = transInfo[i][2];
		float opHeight = transInfo[i][3];
		float opMargin = extraInfo[i][0];

		// op and children cook info
		bool opIsCOMP = bool(extraInfo[i][1]);
		bool opCooking = bool(cookInfo[i][0]);
		float opCookLevel = cookInfo[i][1];
		float opGpuMemLevel = gpuMem[i][0];
		bool opChildrenCooking = bool(cookInfo[i][2]);
		float opChildrenCookLevel = cookInfo[i][3];
		float opChildrenGpuMemLevel = gpuMem[i][1];

		bool _opCooking = !opIsCOMP ? opCooking : opChildrenCooking;
		float _opCookLevel = !opIsCOMP ? opCookLevel : opChildrenCookLevel + opCookLevel;
		float _opGpuMemLevel = !opIsCOMP ? opGpuMemLevel : opChildrenGpuMemLevel;

		// float _720 = 3686400;
		float _opGpuMemLevelRel = _opGpuMemLevel / 100000000;

		// random code that does nothing, but makes this shader work on willy's computer
		if (vUV.s == 27) {
			vec4 willy = vec4(cookInfo[i]);
			frag = vec4(willy);
			return;
		}

		// scale
		float edgeRel = edge * zoom;
		float cookLevelRel = edgeRel * _opCookLevel;
		if (_opCookLevel < 1.0) cookLevelRel = edgeRel;
		if (_opCookLevel > 10.0) cookLevelRel = edgeRel * 10.0;
		float cookGpuMemLevelLevelRel = edgeRel * _opGpuMemLevelRel;
		if (_opGpuMemLevelRel < 1.0) cookGpuMemLevelLevelRel = edgeRel;
		if (_opGpuMemLevelRel > 10.0) cookGpuMemLevelLevelRel = edgeRel * 10.0;

		// bounding area
		float l = opOriginX - opMargin; // left
		float r = opOriginX + opWidth + opMargin; // right
		float tt = opOriginY + opHeight + opMargin + cookLevelRel; // top top
		float tb = opOriginY + opHeight + opMargin; // top bottom
		float bt = opOriginY - opMargin; // bottom top
		float bb = opOriginY - opMargin - cookGpuMemLevelLevelRel; // bottom bottom
		
		// top cook bar (now all ops)
		if ((x > l) && (x < r)) {
			if ((y > tb) && (y < tt)) {
				insideBar = true;
				
				cooking = _opCooking;
				cookLevel = _opCookLevel;
				if (cookLevel > 1) cookLevel = 1;

				// opacity for fade between cook time between 1 and 10
				opacity = 1 - (float(y) - opOriginY - opHeight - opMargin) / (10.0 * edgeRel);
				if (opacity < 0.0) opacity = 0.0;
				if (opacity > 1.0) opacity = 1.0;
				opacity = pow(opacity, 2);

				// Check if inside level bounds
				if (x < opOriginX - opMargin + ((opWidth + opMargin * 2) * _opCookLevel)) {
					insideLevel = true;
				}

				// Check if inside stripe
				float stripeWidth = 15.0;
				float barX = float(x) - opOriginX;						
				float barY = float(y) - opOriginY - opHeight - opMargin;
				float stripePos = (barX + barY) / zoom;
				float stripePosTime = stripePos - float(absTime);
				if (mod(stripePosTime, (stripeWidth * 2)) > stripeWidth) {
					insideStripe = true;
				}

				break;
			}
		}

		// bottom gpu mem bar
		if ((x > l) && (x < r)) {
			if ((y > bb) && (y < bt)) {
				isMem = true;
				insideBar = _opGpuMemLevel > 0;

				cooking = false;
				cookLevel = _opGpuMemLevelRel;
				if (cookLevel > 1) cookLevel = 1;
				
				// opacity for fade between children cook time between 1 and 10
				opacity = 1 - (-(float(y) - opOriginY + opMargin) / (10.0 * edgeRel));
				if (opacity < 0.0) opacity = 0.0;
				if (opacity > 1.0) opacity = 1.0;
				opacity = pow(opacity, 2);

				// Check if inside level bounds
				if (x < opOriginX - opMargin + ((opWidth + opMargin * 2) * _opGpuMemLevelRel)) {
					insideLevel = true;	
				}
				
				// Check if inside stripe
				float stripeWidth = 10;
				float barX = float(x) - opOriginX;
				float barY = float(y) - opOriginY + opMargin;
				float stripePos = (barX - barY) / zoom;
				float stripePosTime = stripePos - float(absTime);
				if (mod(stripePosTime, (stripeWidth * 2)) > stripeWidth) {
					insideStripe = true;
				}

				break;
			}
		}

	}

	// Set Colors
	float lvl = cookLevel * 2;
	if (lvl > 1) lvl = 1;
	float alvl = 1 - ((cookLevel * 2) - 1);
	if (alvl > 1) alvl = 1;
	vec4 levelColor = !isMem ? vec4(lvl, alvl, 0.0, 1.0) : vec4(0.0, alvl, 1.0, 1.0) ;

	// Apply Colors
	vec4 color = bgColor;
	if (insideBar) {
		if (cooking) {
			if (insideLevel) {
				if (insideStripe) {
					color = matte(levelColor, bgColor, opacity);
				} else {
					color = matte(brightness(levelColor, 0.75), bgColor, opacity);
				}
			} else {
				if (insideStripe) {
					color = matte(brightness(levelColor, 0.25 ), bgColor, opacity);
				} else {
					color = matte(brightness(levelColor, 0.2), bgColor, opacity);
				}
			}
		} else {
			if (insideLevel) {
				color = matte(brightness(levelColor, !isMem ? 0.35 : 0.75), bgColor, opacity);
			} else {
				color = matte(brightness(levelColor, !isMem ? 0.2 : 0.2), bgColor, opacity);
			}
		}
	}

	frag = color;
}