// Shader "VertexPostProcessing.glsl"
// Post process Vertex Shader

#include "Default/Header.glsl"

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;
layout (location = 2) in vec3 aNormal;
layout (location = 3) in vec3 aTangent; // Normal

out VS_OUT {
	vec2 texCoord;
} vsOut;

void main(){
	gl_Position = vec4(aPos.x, -aPos.z, 0.0, 1.0);
	
	vsOut.texCoord = aTexCoord;
	vsOut.texCoord.y = 1.0 - vsOut.texCoord.y;
}