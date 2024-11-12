// This will execute once the page loads
function renderPointCloud(points, colors) {
    const scene = new THREE.Scene();
    const geometry = new THREE.BufferGeometry();
    const vertices = new Float32Array(points.length * 3);
    
    for (let i = 0; i < points.length; i++) {
        vertices[i * 3] = points[i][0];
        vertices[i * 3 + 1] = points[i][1];
        vertices[i * 3 + 2] = points[i][2];
    }
    
    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    
    const material = new THREE.PointsMaterial({ size: 0.1, vertexColors: THREE.VertexColors });
    const pointCloud = new THREE.Points(geometry, material);
    scene.add(pointCloud);
    
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);
    
    camera.position.z = 5;
    
    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    
    animate();
}

window.onload = function() {
    const data = window.cloudData; // Assumes data is injected into window object
    if (data) {
        renderPointCloud(data.points, data.colors);
    }
}
