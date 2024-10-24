// TMDb API key and Base URL
const API_KEY = 'ac25e04e9751a85e9d63d646f4de8db4';
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';

let selectedMovieId = null;  // Store selected movie ID

// Function to fetch top 10 movies by genre
async function getTopMoviesByGenre(genreId) {
    const response = await fetch(`${TMDB_BASE_URL}/discover/movie?api_key=${API_KEY}&with_genres=${genreId}&sort_by=popularity.desc&language=en-US&page=1`);
    const data = await response.json();
    return data.results.slice(0, 10); // Top 10 movies
}

// Function to fetch movie suggestions based on user input
async function searchMovies(query) {
    const response = await fetch(`${TMDB_BASE_URL}/search/movie?api_key=${API_KEY}&query=${query}`);
    const data = await response.json();
    return data.results;
}

// Function to fetch recommendations based on the selected movie ID
async function getRecommendations(movieId) {
    const response = await fetch(`${TMDB_BASE_URL}/movie/${movieId}/recommendations?api_key=${API_KEY}`);
    const data = await response.json();
    return data.results.slice(0, 5); // Top 5 recommended movies
}

// Function to fetch movie details including the trailer and cast
async function getMovieDetails(movieId) {
    const response = await fetch(`${TMDB_BASE_URL}/movie/${movieId}?api_key=${API_KEY}&append_to_response=credits,videos`);
    const data = await response.json();
    return data;
}

// Function to display top 10 movies by genre
async function displayMovies(genreId) {
    const movies = await getTopMoviesByGenre(genreId);
    const carousel = document.querySelector('.carousel');
    carousel.innerHTML = '';

    movies.forEach(movie => {
        const movieDiv = document.createElement('div');
        movieDiv.classList.add('carousel-item');
        movieDiv.innerHTML = `
            <img src="https://image.tmdb.org/t/p/w200${movie.poster_path}" alt="${movie.title}">
            <h3>${movie.title}</h3>
        `;
        carousel.appendChild(movieDiv);
    });
}

// Event listener for genre selection change
document.getElementById('genreSelect').addEventListener('change', (event) => {
    const selectedGenre = event.target.value;
    displayMovies(selectedGenre);
});

// Event listener for movie search
document.getElementById('movieSearch').addEventListener('input', async (event) => {
    const query = event.target.value.trim();
    const resultsContainer = document.querySelector('.search-results');
    
    if (query.length > 0) {
        const results = await searchMovies(query);
        resultsContainer.innerHTML = '';
        resultsContainer.style.display = 'block';

        results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.classList.add('result-item');
            resultDiv.innerText = result.title;
            resultDiv.addEventListener('click', () => {
                selectedMovieId = result.id;
                document.getElementById('movieSearch').value = result.title;
                resultsContainer.style.display = 'none';
                document.getElementById('recommendBtn').style.display = 'block'; // Show Recommend button
            });
            resultsContainer.appendChild(resultDiv);
        });
    } else {
        resultsContainer.style.display = 'none';
    }
});

// Event listener for getting recommendations
document.getElementById('recommendBtn').addEventListener('click', async () => {
    const recommendationsContainer = document.querySelector('.recommendations');
    const recommendations = await getRecommendations(selectedMovieId);
    recommendationsContainer.innerHTML = '';

    recommendations.forEach(async (movie, index) => {
        const movieDetails = await getMovieDetails(movie.id);
        const castNames = movieDetails.credits.cast.slice(0, 3).map(castMember => castMember.name).join(', ');
        const trailer = movieDetails.videos.results.find(video => video.type === 'Trailer');
        const imdbRating = movieDetails.vote_average.toFixed(1);  // IMDb rating (rounded to 1 decimal place)
        const releaseDate = movieDetails.release_date;  // Movie release date

        const movieDiv = document.createElement('div');
        movieDiv.classList.add('recommendation-item');
        movieDiv.innerHTML = `
            <h3>${movie.title}</h3>
            <img src="https://image.tmdb.org/t/p/w300${movie.poster_path}" alt="${movie.title}"> <!-- Increased size -->
            <p><strong>IMDb Rating:</strong> ${imdbRating}</p>
            <p><strong>Release Date:</strong> ${releaseDate}</p>
            <p><strong>Cast:</strong> ${castNames}</p>
            <p><strong>Trailer:</strong> ${trailer ? `<a href="https://www.youtube.com/watch?v=${trailer.key}" target="_blank">Watch here</a>` : 'No trailer available'}</p>
        `;

        recommendationsContainer.appendChild(movieDiv);

        // Add a divider after each recommendation, except the last one
        if (index < recommendations.length - 1) {
            const divider = document.createElement('div');
            divider.classList.add('recommendation-divider');
            divider.style.borderTop = "1px solid #ccc"; // Styling for the divider
            divider.style.margin = "10px 0";
            recommendationsContainer.appendChild(divider);
        }
    });
});

// Initial display of movies when page loads
document.addEventListener('DOMContentLoaded', () => {
    displayMovies(28);  // Default genre: Action
});
