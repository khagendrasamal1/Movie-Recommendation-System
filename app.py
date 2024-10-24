import streamlit as st
import pickle
import requests
from streamlit_carousel import carousel
import mysql.connector

# Load the model
with open('movie_recommendation_knn_model.pkl', 'rb') as f:
    loaded_model = pickle.load(f)

# Extract model data
knn = loaded_model['knn_model']
movie_titles = loaded_model['movie_titles']
tfidf_matrix = loaded_model['tfidf_matrix']
indices = loaded_model['indices']


# TMDb API key
API_KEY = 'ac25e04e9751a85e9d63d646f4de8db4'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'


# Function to provide autocomplete suggestions
def autocomplete_suggestions(query, movie_titles):
    query = query.lower()
    return [title for title in movie_titles if query in title.lower()]


# Function to fetch movie details from TMDb
@st.cache_data
def get_movie_details(movie_title):
    response = requests.get(f"{TMDB_BASE_URL}/search/movie", params={
        'api_key': API_KEY,
        'query': movie_title
    })
    data = response.json()
    if data['results']:
        return data['results'][0]  # Return the first matching movie
    return None


# Function to fetch the trailer link
@st.cache_data
def get_trailer(movie_id):
    response = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}/videos", params={'api_key': API_KEY})
    videos = response.json().get('results', [])
    for video in videos:
        if video['site'] == 'YouTube' and video['type'] == 'Trailer':
            return f"https://www.youtube.com/watch?v={video['key']}"  # Return the trailer link
    return None


# Function to fetch cast details
@st.cache_data
def get_cast(movie_id):
    response = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}/credits", params={'api_key': API_KEY})
    cast = response.json().get('cast', [])
    return cast[:5]  # Return top 5 cast members


# Function to fetch the plot summary
@st.cache_data
def get_plot_summary(movie_id):
    response = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params={'api_key': API_KEY})
    movie_data = response.json()
    return movie_data.get('overview', 'No plot summary available.')


# Function to fetch top movies by genre
@st.cache_data
def get_top_movies_by_genre(genre_id):
    try:
        response = requests.get(f"{TMDB_BASE_URL}/discover/movie", params={
            'api_key': API_KEY,
            'with_genres': genre_id,
            'sort_by': 'popularity.desc'
        })
        return response.json().get('results', [])[:5]  # Get top 5 movies for the genre
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch movies for genre ID {genre_id}: {e}")
        return []


# Genre dictionary to map genre names to TMDb IDs
GENRES = {
    "Action": 28,
    "Thriller": 53,
    "Drama": 18,
    "Comedy": 35,
    "Romance": 10749,
    "Fantasy": 14,
    "Horror": 27,
    "Animation": 16
}


# Function to get recommendations
def get_recommendations(title, model_data, n_recommendations=5):
    title = title.lower()
    indices_lower = {k.lower(): v for k, v in model_data['indices'].items()}

    if title not in indices_lower:
        return ["Movie not found in the dataset."]

    idx = indices_lower[title]
    distances, indices = knn.kneighbors(tfidf_matrix[idx], n_neighbors=n_recommendations + 1)
    recommended_movies = [movie_titles.iloc[i] for i in indices.flatten()[1:]]
    return recommended_movies


# Load custom CSS for styling and hover effects
st.markdown('''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rakkas&display=swap" rel="stylesheet">
<style>
.rakkas-regular {
    font-family: "Rakkas", serif;
    font-weight: 700; /* Bold */
    font-size: 64px; /* Increase size */
    text-align: center; /* Center the text */
    color: #ff9900; /* Change color */
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); /* Add shadow */
}
.movie-card {
    border-radius: 10px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
    padding: 10px;
}
.movie-poster {
    width: 100%; /* Ensures it takes full width of the container */
    height: auto; /* Maintains aspect ratio */
    border-radius: 10px; /* For rounded corners */
}
.movie-poster:hover {
    transform: scale(1.05); /* Scale effect on hover */
}
.cast-member {
    display: inline-block; /* Inline block for side-by-side display */
    margin-right: 20px; /* Space between cast members */
}
</style>
''', unsafe_allow_html=True)

# Header with custom class
st.markdown('<div class="rakkas-regular">🎬CinePhile</div>', unsafe_allow_html=True)


# Top Movies by Genre Section
st.write("## 🔥 Trending Movies by Genre 📈")

# Genre selection
selected_genre = st.selectbox("Choose a genre:", list(GENRES.keys()))

if selected_genre:
  genre_id = GENRES[selected_genre]
  top_movies = get_top_movies_by_genre(genre_id)

# Display the top movies for the selected genre
if top_movies:
    st.write(f"### Top 5 {selected_genre} Movies:")

    carousel_items = []
    for movie in top_movies:
        movie_title = movie['title']
        poster_path = movie['poster_path']
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "No image available"

        # Create carousel items with movie title, poster, and empty text
        carousel_items.append({
        "title": movie_title,  # Set the carousel item title
        "img": poster_url,   # Movie poster
        "text": "",          # Empty text for now
        })

    # Display the carousel if there are movies
    if carousel_items:
        st.write(carousel(carousel_items, key="top_movies_carousel"))
    else:
        st.write("No movies found for this genre.")
else:
    st.write("No movies found for this genre.")


# Autocomplete Text Input for movie title
user_input = st.text_input("Enter a movie title to get recommendations:", "")

# Display the autocomplete suggestions below the input
if user_input:
    suggestions = autocomplete_suggestions(user_input, movie_titles)
    if suggestions:
        selected_movie = st.selectbox("Did you mean?", suggestions)
    else:
        st.write("No movie suggestions found.")
else:
    selected_movie = None

# Button to get recommendations based on the selected movie
if st.button("🍿 Recommend 🍿"):
    if selected_movie:
        recommendations = get_recommendations(selected_movie, loaded_model)
        st.write("### Recommended Movies:")
        
        for movie in recommendations:
            movie_details = get_movie_details(movie)
            if movie_details:
                movie_id = movie_details['id']
                poster_path = movie_details['poster_path']
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "No image available"
                
                # Display movie information in a card
                st.markdown(f'<div class="movie-card">', unsafe_allow_html=True)
                st.image(poster_url, width=300, caption=movie)
                
                # Fetch additional information
                release_date = movie_details.get('release_date', 'N/A')
                rating = movie_details.get('vote_average', 'N/A')
                
                # Fetch and display trailer link
                trailer_link = get_trailer(movie_id)

                # Fetch and display cast details
                cast = get_cast(movie_id)
                if cast:
                    cast_details = ", ".join([member['name'] for member in cast])  # Only show actor names
                else:
                    cast_details = "No cast information available."
                
                # Fetch and display plot summary
                plot_summary = get_plot_summary(movie_id)

                # Display movie details
                st.write(f"**Rating:** {rating}/10")
                st.write(f"**Cast:** {cast_details}")
                st.write(f"**Release Date:** {release_date}")
                st.write(f"**Plot Summary:** {plot_summary}")
                
                # Embed the trailer using st.video() if available
                if trailer_link:
                    st.write("**Trailer:**")
                    st.video(trailer_link)  # Embedding the YouTube trailer
                else:
                    st.write("No trailer available.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.write("---")
            else:
                st.write("Movie details not found.")


# Streaming platform dictionary (TMDb provider IDs can be added based on research)
STREAMING_PLATFORMS = {
    "Netflix": 8,
    "Amazon Prime": 9,
    "Hulu": 15,
    "Disney+": 337,
    "Apple TV+": 350,
    "Peacock": 386,
    "Paramount+": 531,
    "Starz": 43
}


# Function to fetch top trending movies by platform
@st.cache_data
def get_trending_movies_by_platform(provider_id):
    try:
        response = requests.get(f"{TMDB_BASE_URL}/discover/movie", params={
            'api_key': API_KEY,
            'with_watch_providers': provider_id,
            'watch_region': 'US',  # You can adjust the region as needed
            'sort_by': 'popularity.desc'
        })
        return response.json().get('results', [])[:5]  # Get top 5 movies for the platform
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch movies for provider ID {provider_id}: {e}")
        return []


# New section for trending movies
st.write("## 🎞️🔥 Trending Movies Across Streaming Platforms")

# Let users select the streaming platform
selected_platform = st.selectbox("Choose a streaming platform:", list(STREAMING_PLATFORMS.keys()))

# If a platform is selected, fetch and display trending movies
if selected_platform:
    platform_id = STREAMING_PLATFORMS[selected_platform]
    trending_movies = get_trending_movies_by_platform(platform_id)

    # Display the trending movies for the selected platform
    if trending_movies:
        st.write(f"### Trending Movies on {selected_platform}:")

        # If using a carousel (only images):
        # Carousel format (uncomment if using a carousel):
        # carousel_items = []
        # for movie in trending_movies:
        #     poster_path = movie['poster_path']
        #     poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "No image available"
            
        #     # Create carousel items with just the image (no title or text)
        #     carousel_items.append({
        #         "title": "",            # Empty title
        #         "img": poster_url,      # Movie poster image
        #         "text": "",             # No text
        #     })

        # if carousel_items:
        #     st.write(carousel(carousel_items, key="platform_movies_carousel"))
        # else:
        #     st.write(f"No trending movies found on {selected_platform}.")

        # If NOT using a carousel, display posters in a grid:
        cols = st.columns(5)  # Display 5 posters per row
        for idx, movie in enumerate(trending_movies):
            poster_path = movie['poster_path']
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "No image available"
            
            # Display movie posters in a grid layout
            with cols[idx % 5]:
                st.image(poster_url, use_column_width=True)
    else:
        st.write(f"No trending movies found on {selected_platform}.")


# Streaming platform dictionary for web series (TMDb provider IDs can be added based on research)
SERIES_STREAMING_PLATFORMS = {
    "Netflix": 8,
    "Amazon Prime": 9,
    "Hulu": 15,
    "Disney+": 337,
    "Apple TV+": 350,
    "Peacock": 386,
    "Paramount+": 531,
    "Starz": 43
}


# Function to fetch top trending web series by platform
@st.cache_data
def get_trending_web_series_by_platform(provider_id):
    try:
        response = requests.get(f"{TMDB_BASE_URL}/discover/tv", params={
            'api_key': API_KEY,
            'with_watch_providers': provider_id,
            'watch_region': 'US',  # You can adjust the region as needed
            'sort_by': 'popularity.desc'
        })
        response.raise_for_status()  # Raise an error for bad responses
        return response.json().get('results', [])[:5]  # Get top 5 series for the platform
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch web series for provider ID {provider_id}: {e}")
        return []


# New section for trending web series
st.write("## 🍿📽️ Trending Web Series Across Streaming Platforms")

# Let users select the streaming platform for web series
selected_series_platform = st.selectbox(
    "Choose a streaming platform:", 
    list(SERIES_STREAMING_PLATFORMS.keys()),
    key='selectbox_series_platform'  # Unique key for selectbox
)

# If a platform is selected, fetch and display trending web series
if selected_series_platform:
    series_platform_id = SERIES_STREAMING_PLATFORMS[selected_series_platform]
    trending_web_series = get_trending_web_series_by_platform(series_platform_id)

    # Display the trending web series for the selected platform
    if trending_web_series:
        st.write(f"### Trending Web Series on {selected_series_platform}:")

        # Display posters in a grid layout
        cols = st.columns(5)  # Display 5 posters per row
        for idx, series in enumerate(trending_web_series):
            poster_path = series.get('poster_path')  # Use get to avoid KeyError
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            
            # Display series posters in a grid layout
            with cols[idx % 5]:
                if poster_url:
                    st.image(poster_url, use_column_width=True)
                else:
                    st.write("No image available")  # Handle missing images
    else:
        st.write(f"No trending web series found on {selected_series_platform}.")