<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">Stock App</router-link>
        <div class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <router-link class="nav-link" to="/">SEC Data Viewer</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/watchlist">Watchlist</router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
    <router-view></router-view>
  </div>
</template>

<script setup>
import 'bootstrap/dist/css/bootstrap.min.css';
</script>

<style>
/* Add any global styles here if needed */
</style>