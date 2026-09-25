// Shader "ProceduralTexture/Sky.glsl"
// Shader "ProceduralTexture/Sky.glsl"
#include "Default/Header.glsl"

#include "Math/Mathutils.glsl"

#include "Math/Perlin.glsl"
#include "Math/Random.glsl"

in VS_OUT{
    vec2 texCoord;
} fsIn;

layout(location = 0) out vec4 gColor;

// Sky parameters
uniform float _timer = 0.0;
uniform vec3  _sunDirection = vec3(0.0, 0.5, -1.0);
uniform vec3  _sunColor = vec3(1.0, 0.8, 0.4);
uniform float _sunIntensity = 1.0;
uniform float sunSize = 0.02; // Size of the sun disk (angular size)
uniform float atmosphereThickness = 1.0; // Density of atmospheric scattering
uniform vec3 rayleighScatteringColor = vec3(0.0, 0.646, 0.929);  // Blue light scattering color
uniform vec3 mieScatteringColor = vec3(1.0, 1.0, 1.0);         // Haze/sunset scattering color
uniform float starBrightnessFactor = 1.0;  // Brightness multiplier for stars at night
uniform float starDensityFactor = 1.0;   // Density of stars in the night sky
uniform float cloudCoverageFactor = 0.35; // Amount of sky covered by clouds (0-1)
uniform float cloudSpeed = 0.6;          // Speed of cloud movement animation
uniform float cloudDensityFactor = 0.5;  // Opacity/thickness of clouds
uniform float cloudPlaneHeight = 3000.0; // Height of cloud plane in meters
uniform vec3 horizonColor = vec3(1.0, 1.0, 1.0);     // Sky color at the horizon during day
uniform vec3 zenithColor = vec3(0.0, 0.283, 0.941);      // Sky color at zenith during day
uniform vec3 nightHorizonColor = vec3(0.08, 0.09, 0.12); // Night sky color at horizon (brighter due to light pollution)
uniform vec3 nightZenithColor = vec3(0.02, 0.025, 0.04);  // Night sky color at zenith (darker)

// Sunrise/Sunset parameters
uniform vec3 sunriseColor = vec3(1.0, 0.4, 0.1);     // Warm orange-red sunrise color
uniform vec3 sunsetColor = vec3(1.0, 0.3, 0.0);      // Deep orange-red sunset color
uniform float sunriseIntensity = 2.0;                // Intensity multiplier for sunrise effects
uniform float sunsetIntensity = 2.5;                 // Intensity multiplier for sunset effects
uniform float horizonGlowSize = 0.3;                 // Size of horizon glow effect
uniform float cloudSunlightBoost = 1.5;              // Brightness boost for clouds in sunlight

// Night sky parameters
uniform float nightBrightnessFactor = 0.3;           // Overall night brightness multiplier (0-1)
uniform float nightCloudBrightnessFactor = 0.15;     // Night cloud brightness multiplier (0-1)
uniform float nightHorizonFadeFactor = 0.8;          // Horizon fade strength for stars/clouds at night (0-1)
uniform vec3 nightGroundColor = vec3(0.01, 0.01, 0.015); // Very dark ground color for IBL
uniform float nightContrastFactor = 0.2;             // Night cloud contrast reduction (0-1)

// Atmosphere scattering constants
const float EARTH_RADIUS = 6371000.0;
const float ATMOSPHERE_HEIGHT = 100000.0;
const vec3 EARTH_CENTER = vec3(0.0, -EARTH_RADIUS, 0.0);

// Smooth interpolation
float SmoothStep(float t) {
    return t * t * (3.0 - 2.0 * t);
}

// Calculate atmospheric scattering with enhanced sunrise/sunset effects
vec3 CalculateAtmosphere(vec3 rayDir, vec3 lightDir, float sunIntensity) {
    if (sunIntensity < 0.01) {
        return vec3(0.0); // No atm contribution at night
    }
    
    vec3 normalizedLightDir = normalize(lightDir);
    float cosTheta = dot(rayDir, normalizedLightDir);

    // Rayleigh scattering (blue sky)
    float rayleighPhase = (3.0 / (16.0 * PI)) * (1.0 + cosTheta * cosTheta);
    vec3 rayleighColor = rayleighScatteringColor * rayleighPhase;

    // Mie scattering (haze/sunset effects)
    float g = 0.76;
    float g2 = g * g;
    float miePhase = (3.0 / (8.0 * PI)) * ((1.0 - g2) * (1.0 + cosTheta * cosTheta)) /
        ((2.0 + g2) * pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5));
    vec3 mieColor = mieScatteringColor * miePhase;

    float height = max(0.0, rayDir.y);
    float density = exp(-height * atmosphereThickness);
    float sunHeight = normalizedLightDir.y;
    float horizonFactor = 1.0 - smoothstep(-0.15, 0.15, sunHeight);
    
    float sunAzimuth = (abs(normalizedLightDir.x) < 0.001 && abs(normalizedLightDir.z) < 0.001) ? 
                       0.0 : atan(normalizedLightDir.z, normalizedLightDir.x);
    float isEarlyDay = step(0.0, cos(sunAzimuth)); // Simple east/west determination
    
    vec3 goldenHourColor = mix(sunsetColor, sunriseColor, isEarlyDay);
    float goldenHourIntensity = mix(sunsetIntensity, sunriseIntensity, isEarlyDay);
    
    // Enhanced horizon glow during golden hour
    float horizonDistance = abs(rayDir.y);
    float horizonGlow = exp(-horizonDistance / horizonGlowSize) * horizonFactor;
    
    // Base sky color
    vec3 skyColor = mix(horizonColor, zenithColor, height);
    vec3 goldenHorizon = mix(skyColor, goldenHourColor * goldenHourIntensity, horizonGlow);
    skyColor = mix(skyColor, goldenHorizon, horizonFactor);
    
    // Enhanced atm persp during golden hour
    float atmosphericEnhancement = 1.0 + horizonFactor * 0.5;    
    return (skyColor + rayleighColor + mieColor) * density * sunIntensity * atmosphericEnhancement;
}

// Generate sun disk
vec3 CalculateSun(vec3 rayDir, vec3 lightDir, vec3 sunColor, float sunIntensity, float sunSize) {
    vec3 normalizedLight = normalize(lightDir);
    float sunDist = distance(rayDir, normalizedLight);

    float sunMask = 1.0 - smoothstep(sunSize * 0.5, sunSize, sunDist);
    float coronaMask = 1.0 / (1.0 + sunDist * sunDist * 100.0);
    coronaMask = pow(coronaMask, 2.0);

    vec3 sunResult = sunColor * sunIntensity * (sunMask + coronaMask * 0.3);

    // Add lens flare effect
    float flare = max(0.0, 1.0 - sunDist * 20.0);
    sunResult += sunColor * flare * flare * 0.1;
    return sunResult;
}

// Generate star field
vec3 CalculateStars(vec3 rayDir, float nightFactor) {
    if (nightFactor < 0.1) return vec3(0.0);
    if (rayDir.y < 0.0) return vec3(0.0);

    vec3 starPos = rayDir * 1000.0;

    float stars = 0.0;

    // Create clustering bias using noise
    float clusterBias1 = Noise3D(starPos * 0.02) * 0.7 + 0.3; // Large scale clusters
    float clusterBias2 = Noise3D(starPos * 0.08) * 0.5 + 0.5; // Medium scale variation
    float totalClusterBias = clusterBias1 * clusterBias2;

    // Large bright stars
    vec3 cell1 = floor(starPos * starDensityFactor * 0.1);
    float threshold1 = mix(0.95, 0.88, totalClusterBias); // Variable threshold based on clustering
    if (Random(cell1) > threshold1) {
        vec2 localPos = fract(starPos.xy * starDensityFactor * 0.1) - 0.5;
        float starDist = length(localPos);
        if (starDist < 0.03) {
            stars += (1.0 - starDist / 0.03) * 5.0;
        }
    }

    // Medium stars
    vec3 cell2 = floor(starPos * starDensityFactor * 0.5);
    float threshold2 = mix(0.92, 0.84, totalClusterBias);
    if (Random(cell2) > threshold2) {
        vec2 localPos = fract(starPos.xy * starDensityFactor * 0.5) - 0.5;
        float starDist = length(localPos);
        if (starDist < 0.015) {
            stars += (1.0 - starDist / 0.015) * 3.0;
        }
    }

    // Small stars
    vec3 cell3 = floor(starPos * starDensityFactor);
    float threshold3 = mix(0.90, 0.80, totalClusterBias);
    if (Random(cell3) > threshold3) {
        vec2 localPos = fract(starPos.xy * starDensityFactor) - 0.5;
        float starDist = length(localPos);
        if (starDist < 0.008) {
            stars += (1.0 - starDist / 0.008) * 2.0;
        }
    }

    // Tiny stars
    vec3 cell4 = floor(starPos * starDensityFactor * 2.0);
    float threshold4 = mix(0.88, 0.75, totalClusterBias);
    if (Random(cell4) > threshold4) {
        vec2 localPos = fract(starPos.xy * starDensityFactor * 2.0) - 0.5;
        float starDist = length(localPos);
        if (starDist < 0.003) {
            stars += (1.0 - starDist / 0.003) * 1.2;
        }
    }

    // Add twinkling effect
    float twinkle = 0.8 + 0.2 * sin(_timer * 3.0 + Random(starPos) * 100.0);
    
    // Add horizon fading for stars at night
    float horizonFade = smoothstep(0.0, 0.2, rayDir.y); // Fade stars near horizon
    horizonFade = mix(1.0, horizonFade, nightHorizonFadeFactor);

    return vec3(stars * starBrightnessFactor * nightFactor * twinkle * horizonFade);
}

vec3 CalculateClouds(vec3 rayDir) {
    if (rayDir.y < 0.0) return vec3(0.0); // Strict horizon cutoff
    
    float initialHorizonFade = 1.0;
    if (rayDir.y < 0.02) {
        initialHorizonFade = smoothstep(0.0, 0.02, rayDir.y);
        initialHorizonFade = initialHorizonFade * initialHorizonFade; // Quadratic for sharper cutoff
        if (initialHorizonFade < 0.001) return vec3(0.0);
    }

    vec3 cameraPos = vec3(0.0, 0.0, 0.0);
    float planeY = cloudPlaneHeight;

    // Calculate ray-plane intersection
    float safeRayY = max(abs(rayDir.y), 0.001); // Ensure minimum value to prevent huge t values
    float t = planeY / safeRayY;
    t = min(t, 100000.0); // Cap maximum distance
    
    vec3 intersectionPoint = cameraPos + t * rayDir;

    // Use intersection point for cloud sampling
    vec2 cloudPos = intersectionPoint.xz;

    // Density affects noise scale: higher density = larger clouds (smaller scale values)
    float densityScale = mix(2.0, 0.5, cloudDensityFactor);
    float detailAmount = mix(0.4, 0.15, cloudDensityFactor);
    
    float baseScale = 0.0002 * densityScale;
    float cloudNoise = FractalNoise3D(vec3(cloudPos.x, planeY, cloudPos.y) * baseScale, _timer * cloudSpeed, 4, 0.5);
    float turbulence1 = FractalNoise3D(vec3(cloudPos.x, planeY, cloudPos.y) * (baseScale * 4.0), _timer * cloudSpeed * 1.2, 3, 0.4) * detailAmount;
    float turbulence2 = FractalNoise3D(vec3(cloudPos.x, planeY + 500.0, cloudPos.y) * (baseScale * 10.0), _timer * cloudSpeed * 0.8, 2, 0.6) * (detailAmount * 0.5);
    cloudNoise += turbulence1 + turbulence2;

    float coverageThreshold = (1.0 - cloudCoverageFactor) * 1.2 - 0.1;

    float densityInfluence = mix(0.3, 0.1, cloudDensityFactor);
    float cloudMask = smoothstep(coverageThreshold - densityInfluence, coverageThreshold + densityInfluence * 2.0, cloudNoise);
    float density = cloudMask * mix(0.3, 1.5, cloudDensityFactor);

    float distance = length(intersectionPoint.xz);
    float distanceFalloff = 1.0 / (1.0 + distance * 0.00005);
    distanceFalloff = mix(0.3, 1.0, distanceFalloff);
    density *= distanceFalloff;
    if (density < 0.01) return vec3(0.0);

    vec3 sunDir = normalize(_sunDirection);

    vec3 sunProjected = vec3(sunDir.x, 0.0, sunDir.z);
    float projectedLength = length(sunProjected);
    vec3 cloudToSun = (projectedLength < 0.001) ? vec3(1.0, 0.0, 0.0) : normalize(sunProjected);
    
    vec3 rayToCloud = normalize(vec3(rayDir.x, 0.0, rayDir.z));
    float sunAlignment = dot(rayToCloud, cloudToSun);

    // Base cloud color
    vec3 cloudColor = vec3(1.0, 1.0, 1.0);

    // Calculate day/night factors
    float sunHeight = normalize(_sunDirection).y;
    float dayFactor = smoothstep(-0.1, 0.1, sunHeight);
    float nightFactor = 1.0 - dayFactor;

    // Daytime cloud lighting with intensity protection
    float sunIllumination = (sunAlignment + 1.0) * 0.5; // Normalize to 0-1
    
    // Calculate enhanced sunrise/sunset lighting for clouds
    float horizonFactor = 1.0 - smoothstep(-0.15, 0.15, sunHeight);
    vec3 normalizedSunDir = normalize(_sunDirection);
    float sunAzimuth = (abs(normalizedSunDir.x) < 0.001 && abs(normalizedSunDir.z) < 0.001) ? 
                       0.0 : atan(normalizedSunDir.z, normalizedSunDir.x);
    float isEarlyDay = step(0.0, cos(sunAzimuth));
    vec3 goldenHourColor = mix(sunsetColor, sunriseColor, isEarlyDay);
    
    vec3 baseSunlitColor = mix(vec3(0.7, 0.7, 0.8), _sunColor * 1.3, sunIllumination * 0.5);
    vec3 goldenCloudColor = mix(baseSunlitColor, goldenHourColor * cloudSunlightBoost, horizonFactor * sunIllumination);
    
    float clampedSunIntensity = min(_sunIntensity, 3.0); // Cap the intensity effect on clouds
    vec3 sunlitColor = goldenCloudColor * mix(1.0, clampedSunIntensity, 0.3); // Reduce intensity impact
    sunlitColor *= dayFactor;

    // Nighttime cloud lighting - much darker and lower contrast
    vec3 nightAmbient = vec3(0.08, 0.09, 0.12) * nightCloudBrightnessFactor;
    vec3 moonlitColor = mix(vec3(0.06, 0.07, 0.1), vec3(0.12, 0.13, 0.16), sunIllumination * nightContrastFactor);
    vec3 nightCloudColor = moonlitColor * nightFactor * nightCloudBrightnessFactor;
    
    // Add horizon fading for clouds at night
    float cloudHorizonFade = smoothstep(0.0, 0.15, rayDir.y);
    cloudHorizonFade = mix(1.0, cloudHorizonFade, nightHorizonFadeFactor * nightFactor);
    
    if (nightFactor > 0.5) {
        density *= 2.0 * cloudHorizonFade; // More opaque at night but fade at horizon
    }

    // Combine day and night lighting
    vec3 finalCloudColor = sunlitColor + nightCloudColor;

    // Cloud shadows using secondary noise
    float shadowNoise = FractalNoise3D(vec3(cloudPos.x, planeY + 200.0, cloudPos.y) * 0.0004, _timer * cloudSpeed * 0.6, 2, 0.7);
    float shadowFactor = mix(0.3, 1.0, shadowNoise);

    // Self-shadowing based on density
    shadowFactor *= (1.0 - density * 0.3);

    cloudColor = finalCloudColor * shadowFactor;

    // Atmospheric perspective based on distance and height
    float atmosphericFactor = 1.0 - exp(-distance * 0.00002);
    vec3 atmosphereColor = mix(vec3(1.0, 1.0, 1.0), vec3(0.8, 0.85, 1.0), atmosphericFactor);
    cloudColor *= atmosphereColor;

    // Fade clouds near horizon for depth perception
    float horizonFade = smoothstep(0.0, 0.15, rayDir.y);
    density *= mix(0.4, 1.0, horizonFade);

    cloudColor *= cloudHorizonFade;    
    cloudColor *= initialHorizonFade;
    density *= initialHorizonFade;

    return cloudColor * density;
}

// Main sky calculation
vec3 CalculateSkyColor(vec2 uv) {
    // Convert UV to world direction
    vec2 sphereUV = uv * 2.0 - 1.0;

    // Convert to 3D direction (spherical coordinates)
    float phi = sphereUV.x * PI;
    float theta = sphereUV.y * PI * 0.5;

    vec3 rayDir = vec3(
        cos(theta) * sin(phi),
        sin(theta),
        cos(theta) * cos(phi)
    );

    // Calculate sun position
    vec3 normalizedSunDir = normalize(_sunDirection);
    float sunHeight = normalizedSunDir.y;

    // Night factor based on sun height
    float nightFactor = smoothstep(0.1, -0.1, sunHeight);
    float dayFactor = 1.0 - nightFactor;

    vec3 atmosphere = CalculateAtmosphere(rayDir, _sunDirection, _sunIntensity * dayFactor);
    vec3 sun = CalculateSun(rayDir, _sunDirection, _sunColor, _sunIntensity * dayFactor, sunSize);
    vec3 stars = CalculateStars(rayDir, nightFactor);
    vec3 clouds = CalculateClouds(rayDir);

    vec3 nightSky = mix(nightHorizonColor, nightZenithColor, abs(rayDir.y));

    // Combine all elements with proper alpha blending
    vec3 finalColor = mix(nightSky, atmosphere, dayFactor);
    finalColor += sun;
    
    finalColor *= (dayFactor + nightFactor * nightBrightnessFactor);
    
    if (rayDir.y < 0.0) {
        float groundDepth = abs(rayDir.y); // How far below horizon (0 to 1)
        float groundFade = mix(1.0, 1.0 - groundDepth * groundDepth, nightFactor);
        finalColor *= groundFade;
        
        // Additional darkening for IBL at night
        vec3 groundDarkening = mix(vec3(1.0), nightGroundColor / max(nightHorizonColor, vec3(0.001)), nightFactor * groundDepth);
        finalColor *= groundDarkening;
    }
    
    vec3 starsContribution = stars * (dayFactor + nightFactor * nightBrightnessFactor);
    finalColor += starsContribution;
    
    float cloudAlpha = min(length(clouds) * 2.0, 1.0);
    if (cloudAlpha > 0.001) {
        vec3 normalizedClouds = clouds / max(length(clouds), 0.001);
        finalColor = mix(finalColor, normalizedClouds, cloudAlpha);
    }
    return max(vec3(0.0), finalColor);
}

void main() {
    vec2 uv = fsIn.texCoord;
    uv.y = 1 - uv.y;
    vec3 skyColor = CalculateSkyColor(uv);
    gColor = vec4(skyColor, 1.0);
}