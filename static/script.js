document.addEventListener('DOMContentLoaded', async function () {
    const giftCount = document.getElementById('gift-number');
    const categoryContainer = document.getElementById('category-container');
    const subcategoryContainer = document.getElementById('subcategory-container');
    const subcategoryTitle = document.getElementById('subcategory-title');
    const subcategoryCells = document.querySelectorAll('.subcategory-cell');
    const languageSelect = document.getElementById('language-select');

    const translationForm = document.getElementById('translation-form');
    const translationLabel = document.getElementById('translation-label');
    const translationInput = document.getElementById('translation');
    const submitButton = document.getElementById('submit-button');
    const giftMessage = document.getElementById('gift-message');

    let categories = []; 
    let languages = [];
    let selectedSubcategoryCell = null;
    let selectedLanguage = null;
    let selectedCategoryCell = null; // Ajout pour gérer la sélection de catégorie

    // Fonction pour récupérer les données depuis la base de données
    async function fetchData() {
        try {
            const response = await fetch('https://gabonlanguage.onrender.com/categorie/');
            const categoriesData = await response.json();
            categories = categoriesData.categories;

            const langResponse = await fetch('https://gabonlanguage.onrender.com/langue/');
            const langData = await langResponse.json();
            languages = langData.languages;

            generateCategories();
            populateLanguages();
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }

    await fetchData();

    // Fonction pour générer les cellules de catégories
    function generateCategories() {
        categories.forEach(category => {
            const cell = document.createElement('div');
            cell.className = 'category-cell';
            const categoryUrl = category.url;
            cell.innerHTML = `<img src="${categoryUrl}" alt="${category.nom}" class="category-icon"> ${category.nom}`;
            cell.addEventListener('click', () => selectCategory(category, cell)); // Ajout du cell pour la sélection visuelle
            categoryContainer.appendChild(cell);
        });
    }

    // Fonction pour sélectionner une catégorie et afficher les sous-catégories
    function selectCategory(selectedCategory, cell) {
        if (selectedCategoryCell) {
            selectedCategoryCell.classList.remove('selected-category');
        }

        selectedCategoryCell = cell;
        selectedCategoryCell.classList.add('selected-category');

        subcategoryContainer.innerHTML = '';
        translationInput.style.display = 'none';
        submitButton.style.display = 'none';
        giftMessage.style.display = 'none';
        translationLabel.style.display = 'none'; 
        subcategoryTitle.classList.remove('hidden');
        subcategoryContainer.classList.remove('hidden');
        languageSelect.classList.remove('hidden'); 

        if (Array.isArray(selectedCategory.sous_categories)) {
            selectedCategory.sous_categories.forEach(subcategory => {
                const subCell = document.createElement('div');
                subCell.className = 'subcategory-cell';
                subCell.innerHTML = `<img src="${subcategory.url}" alt="${subcategory.nom}" class="category-icon"> ${subcategory.nom}`;
                subCell.addEventListener('click', () => selectSubcategory(subcategory.nom, subCell));
                subcategoryContainer.appendChild(subCell);
            });
        }
    }

    // Fonction pour sélectionner une sous-catégorie et afficher le formulaire de traduction
    function selectSubcategory(subcategoryName, subCell) {
        if (selectedSubcategoryCell) {
            selectedSubcategoryCell.classList.remove('selected-subcategory');
        }

        selectedSubcategoryCell = subCell;
        selectedSubcategoryCell.classList.add('selected-subcategory');
        showTranslationForm();
        translationInput.value = ''; 
    }

    // Fonction pour remplir le combobox de langues
    function populateLanguages() {
        languages.forEach(language => {
            const option = document.createElement('option');
            option.value = language.nom;
            option.textContent = language.nom;
            languageSelect.appendChild(option);
        });

        languageSelect.addEventListener('change', function () {
            selectedLanguage = this.value;
        });
    }

    // Fonction pour afficher le formulaire de traduction
    function showTranslationForm() {
        translationForm.style.display = 'flex';
        translationLabel.style.display = 'block';
        translationInput.style.display = 'block';
        submitButton.style.display = 'block';
        giftMessage.style.display = 'none';
    }

    // Gérer le clic sur le bouton de soumission
    submitButton.addEventListener('click', async function (e) {
        e.preventDefault();

        const translationValue = translationInput.value.trim();
        const selectedCategory = document.querySelector('.category-cell.selected-category');
        const selectedSubcategory = selectedSubcategoryCell ? selectedSubcategoryCell.innerText.trim() : null;

        if (translationValue && selectedLanguage && selectedCategory && selectedSubcategory) {
            try {
                const data = {
                    categorie: selectedCategory ? selectedCategory.innerText.trim() : '',
                    sous_categorie: selectedSubcategory,
                    langue: selectedLanguage,
                    traduction: translationValue
                };

                const response = await fetch('https://gabonlanguage.onrender.com/api/traduction/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    let currentGiftCount = parseInt(giftCount.innerText);
                    currentGiftCount++;
                    giftCount.innerText = currentGiftCount;

                    const giftEmoji = '🎁';
                    giftMessage.innerHTML = `${giftEmoji} Félicitations, vous avez gagné un cadeau ! 🎉`;
                    giftMessage.classList.remove('hidden');
                    giftMessage.style.display = 'block';
                    translationInput.value = '';
                    giftMessage.style.color = "";
                } else {
                    throw new Error('Erreur lors de l\'envoi des données.');
                }
            } catch (error) {
                giftMessage.innerHTML = "Une erreur est survenue lors de l'envoi de la traduction.";
                giftMessage.style.color = "red";
                giftMessage.classList.remove('hidden');
                giftMessage.style.display = 'block';
                console.error('Erreur:', error);
            }
        } else {
            giftMessage.innerHTML = "Veuillez entrer une traduction, sélectionner une langue, une catégorie et une sous-catégorie.";
            giftMessage.style.color = "red";
            giftMessage.classList.remove('hidden');
            giftMessage.style.display = 'block';
        }
    });

    
});
