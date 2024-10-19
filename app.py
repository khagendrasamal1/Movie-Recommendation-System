import pickle
import streamlit as st
import requests


# Function to download file from Google Drive
def download_file_from_google_drive(file_id, dest_path):
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(download_url)
    
    if response.status_code == 200:
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return dest_path
    else:
        st.error(f"Failed to download the file with ID {file_id}.")
        return None


# Google Drive file IDs
movies_list_file_id = "1oyxP7RSpzVNsYTPa_q00KgLrLQKwR9z1"  
similarity_file_id = "10HP-8zWIwbVxv3Ic2LWuMomxcIXqr26Q"

# Define paths where the files will be saved locally
movies_list_path = "movies_list.pkl"
similarity_path = "similarity.pkl"

# Download pickle files from Google Drive
download_file_from_google_drive(movies_list_file_id, movies_list_path)
download_file_from_google_drive(similarity_file_id, similarity_path)

# Load Data from the downloaded pickle files with error handling
try:
    with open(movies_list_path, 'rb') as movies_file:
        movies = pickle.load(movies_file)
    
    with open(similarity_path, 'rb') as similarity_file:
        similarity = pickle.load(similarity_file)

    st.success("Pickle files loaded successfully!")
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
st.markdown('''
    <link rel="preconnect" href="https://fonts.googleapis.com">
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
    </style>
''', unsafe_allow_html=True)

# Header with custom font, centered and larger
st.markdown('<h1 class="rakkas-regular">🎬 CinePhile</h1>', unsafe_allow_html=True)


# Function to Fetch Poster from TMDb
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    try:
        data = requests.get(url, timeout=10).json()
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
        st.error(f"An error occurred: {e}")
        return None


# Function to Fetch Movie Details
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    data = requests.get(url).json()
    genre = ', '.join([g['name'] for g in data['genres']])
    release_date = data['release_date']
    vote_average = data['vote_average']
    overview = data['overview']
    return genre, release_date, vote_average, overview


# Function to Fetch Cast
def fetch_cast(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key=c7ec19ffdd3279641fb606d19ceb9bb1"
    data = requests.get(url).json()
    cast = [actor['name'] for actor in data['cast'][:5]]
    return ', '.join(cast)


# Function to Fetch Trailers from YouTube
def fetch_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    data = requests.get(url).json()
    if data['results']:
        video_key = data['results'][0]['key']
        trailer_url = f"https://www.youtube.com/watch?v={video_key}"
        return trailer_url
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
                st.image(movie_poster[i], use_column_width=True)
                
                # Fetch Movie Details
                genre, release_date, rating, overview = fetch_movie_details(movies[movies['title'] == movie_name[i]].iloc[0].id)
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
                st.write(f"**Cast:** {cast}")
                st.markdown("---")  # Divider between movies


# Function to Fetch Popular Movies
def fetch_popular_movies():
    url = "https://api.themoviedb.org/3/movie/popular?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US&page=1"
    data = requests.get(url).json()
    popular_movies = [(movie['title'], movie['poster_path'], movie['id']) for movie in data['results'][:5]]
    return popular_movies


# Display Popular/Trending Movies Section
st.subheader("🔥Trending Movies🔥")
popular_movies = fetch_popular_movies()
for title, poster, movie_id in popular_movies:
    st.image(f"https://image.tmdb.org/t/p/w500/{poster}", caption=title)

    # Fetch and Display Movie Details
    genre, release_date, rating, overview = fetch_movie_details(movie_id)
    st.write(f"**Genre:** {genre}")
    st.write(f"**Release Date:** {release_date}")
    st.write(f"**Rating:** {rating}/10")
    st.write(f"**Synopsis:** {overview}")

    # Fetch and Display Cast Information
    cast = fetch_cast(movie_id)
    st.write(f"**Cast:** {cast}")
    st.markdown("---")  # Divider between movies

# Improved UI with CSS
st.markdown('''
    <style>
    .movie-poster {
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .movie-text {
        font-weight: bold;
        color: #ff9900;
        font-size: 16px;
        margin-top: 5px;
    }
    </style>
''', unsafe_allow_html=True)
