<script>
    export let spinnerSizePx=15
    export let borderRadiusPercent=50
</script>

<div class="spinner" style="width: {spinnerSizePx}px; height: {spinnerSizePx}px; border-radius: {borderRadiusPercent}%;">
</div>

<style>
    .spinner {
      border: 4px solid #ccc;
      border-top-color: #3498db;
      animation: spin 0.8s linear infinite;
    }
  
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  </style>
  
  