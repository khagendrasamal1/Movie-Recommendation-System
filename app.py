import pickle
import streamlit as st
import requests
import gdown  # Import gdown to download files from Google Drive

# Define Google Drive file IDs and local paths where the files will be saved
movies_list_url = "https://drive.google.com/uc?id=1khkhAsNVKm9RSsDee07lwo_h4PB0DzQf"
similarity_url = "https://drive.google.com/uc?id=1f4HHb6L6AuprNdOwEYQSP1kWrJ5Hzw-G"
movies_list_path = "movies_list.pkl"
similarity_path = "similarity.pkl"

# Download Data from Google Drive
try:
    gdown.download(movies_list_url, movies_list_path, quiet=False)
    gdown.download(similarity_url, similarity_path, quiet=False)
except Exception as e:
    st.error(f"Failed to download files from Google Drive: {e}")
    st.stop()  # Stop execution if files cannot be downloaded

# Load Data from the downloaded pickle files with error handling
try:
    with open(movies_list_path, 'rb') as movies_file:
        movies = pickle.load(movies_file)

    with open(similarity_path, 'rb') as similarity_file:
        similarity = pickle.load(similarity_file)

except (pickle.UnpicklingError, EOFError) as e:
    st.error(f"Failed to load pickle files: {e}")
    st.stop()  # Stop execution if files cannot be loaded
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    st.stop()

# Ensure that the `movies` and `similarity` variables are defined and accessible
if 'movies' not in locals() or 'similarity' not in locals():
    st.error("Movies or similarity data not loaded properly. Please check the files.")
    st.stop()

movies_list = movies['title'].values

# Load custom CSS
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
.movie-poster {
    border-radius: 10px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
''', unsafe_allow_html=True)

# Header with custom font, centered and larger
st.markdown('<h1 class="rakkas-regular">🎬 CinePhile</h1>', unsafe_allow_html=True)


# Function to Fetch Poster from TMDb
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError if the response code is 4xx or 5xx
        data = response.json()
        poster_path = data['poster_path']
        if poster_path:
            full_path = f"https://image.tmdb.org/t/p/w500/{poster_path}"
            return full_path
        else:
            st.error("Poster not found.")
            return None
    except requests.exceptions.Timeout:
        st.error("Request to TMDb timed out. Please try again later.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching the poster: {e}")
        return None


# Function to Fetch Movie Details
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors
        data = response.json()
        genre = ', '.join([g['name'] for g in data['genres']])
        release_date = data['release_date']
        vote_average = data['vote_average']
        overview = data['overview']
        return genre, release_date, vote_average, overview
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching movie details: {e}")
        return None, None, None, None


# Function to Fetch Cast
def fetch_cast(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key=c7ec19ffdd3279641fb606d19ceb9bb1"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors
        data = response.json()
        cast = [actor['name'] for actor in data['cast'][:5]]
        return ', '.join(cast)
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching cast information: {e}")
        return None


# Function to Fetch Trailers from YouTube
def fetch_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors
        data = response.json()
        if data['results']:
            video_key = data['results'][0]['key']
            trailer_url = f"https://www.youtube.com/watch?v={video_key}"
            return trailer_url
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching the trailer: {e}")
    return None


# Function for Movie Recommendations
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distance = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])
    recommend_movie = []
    recommend_poster = []
    for i in distance[1:6]:
        movies_id = movies.iloc[i[0]].id
        recommend_movie.append(movies.iloc[i[0]].title)
        recommend_poster.append(fetch_poster(movies_id))
    return recommend_movie, recommend_poster


# Search Box with Autocomplete
search_query = st.text_input("Search for a movie🔍", "")
if search_query:
    filtered_movies = [movie for movie in movies_list if search_query.lower() in movie.lower()]
else:
    filtered_movies = movies_list

selected_movie = st.selectbox("Select a movie", filtered_movies)


# Show Movie Recommendations on Button Click
if st.button("🍿Show Recommend🍿"):
    with st.spinner("Fetching movie recommendations..."):
        if selected_movie:
            movie_name, movie_poster = recommend(selected_movie)
            for i in range(5):
                st.subheader(movie_name[i])
                # Use HTML for image styling
                st.markdown(f'<img src="{movie_poster[i]}" style="border-radius: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); width: 100%;" alt="{movie_name[i]}">', unsafe_allow_html=True)

                # Fetch Movie Details
                genre, release_date, rating, overview = fetch_movie_details(movies[movies['title'] == movie_name[i]].iloc[0].id)
                if genre:
                    st.write(f"**Genre:** {genre}")
                    st.write(f"**Release Date:** {release_date}")
                    st.write(f"**Rating:** {rating}/10")
                    st.write(f"**Synopsis:** {overview}")

                    # Fetch and Display Trailer
                    trailer_url = fetch_trailer(movies[movies['title'] == movie_name[i]].iloc[0].id)
                    if trailer_url:
                        st.write("**Trailer:**")
                        st.video(trailer_url)

                    # Display Cast Information
                    cast = fetch_cast(movies[movies['title'] == movie_name[i]].iloc[0].id)
                    if cast:
                        st.write(f"**Cast:** {cast}")
                st.markdown("---")  # Divider between movies


# Function to Fetch Popular Movies
def fetch_popular_movies():
    url = "https://api.themoviedb.org/3/movie/popular?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US&page=1"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors
        data = response.json()
        popular_movies = [(movie['title'], movie['poster_path'], movie['id']) for movie in data['results'][:5]]
        return popular_movies
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching popular movies: {e}")
        return []


# Display Popular/Trending Movies Section
st.subheader("🔥Trending Movies🔥")
popular_movies = fetch_popular_movies()
for title, poster, movie_id in popular_movies:
    st.image(f"https://image.tmdb.org/t/p/w500/{poster}", caption=title, use_column_width=True)

    # Fetch and Display Movie Details
    genre, release_date, rating, overview = fetch_movie_details(movie_id)
    if genre:
        st.write(f"**Genre:** {genre}")
        st.write(f"**Release Date:** {release_date}")
        st.write(f"**Rating:** {rating}/10")
        st.write(f"**Synopsis:** {overview}")

        # Fetch and Display Cast Information
        cast = fetch_cast(movie_id)
        if cast:
            st.write(f"**Cast:** {cast}")
    st.markdown("---")  # Divider between movies
