# Thien An Nguyen — Art Portfolio

A Jekyll-based portfolio site for [thienannguyen.github.io](https://thienannguyen.github.io). Content is driven by data files and Markdown so you can add or edit work without touching HTML.

## How to add or edit content

### Add a new artwork

1. **Add your image**  
   Put the image in `assets/images/` (e.g. `assets/images/my-painting.jpg`).

2. **Add an entry in `_data/portfolio.yml`**  
   Append a new item like this:

   ```yaml
   - title: "My painting"
     image: "/assets/images/my-painting.jpg"
     year: "2025"
     medium: "Oil on canvas"
     description: "Optional short caption."
   ```

   - `title` and `image` are required.  
   - `year`, `medium`, `description` are optional.  
   - Order in the file = order in the gallery.

### Change site text and links

- **Navigation, contact links, about text**  
  Edit `_data/site.yml`. Update `nav`, `contact`, `about_intro`, and `about_rest` to match your info (email, Instagram, Behance, etc.).

### Change site title or description

- Edit `_config.yml`: `title`, `description`, `author`.

### Styling

- **Colors, fonts, spacing**  
  Edit `assets/css/main.css`. Variables at the top (e.g. `--accent`, `--bg`) control the look.

## Run the site locally

```bash
bundle install
bundle exec jekyll serve
```

Open [http://localhost:4000](http://localhost:4000). Changes to content and CSS will show after a refresh (or automatically with Jekyll’s watch).

## Publish on GitHub Pages

1. Push this repo to `https://github.com/thienannguyen/thienannguyen.github.io`.
2. In the repo: **Settings → Pages**.
3. Under “Build and deployment”, set **Source** to **Deploy from a branch**, choose your branch (e.g. `main`) and folder **/ (root)**. GitHub will build the Jekyll site for you.

Your site will be live at **https://thienannguyen.github.io**.
