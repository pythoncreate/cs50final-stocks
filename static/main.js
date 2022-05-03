const search = document.getElementById('search');
const matchList = document.getElementById('match-list');

//search states.json and filter it
const searchStates = async searchText => {
    const res = await fetch('./static/data/tickers.json');
    const tickers = await res.json();

    // Get matches to current text input
    let matches = tickers.filter(ticker=> {
        const regex = new RegExp(`^${searchText}`, 'gi');
        return ticker.Name.match(regex) || ticker.Symbol.match(regex);
    });

    if(searchText.length === 0) {
        matches=[];
        matchList.innerHTML='';
    }

    outputHtml(matches);
};

    //show results in html
    const outputHtml = matches => {
        if(matches.length>0) {
            const html = matches.map(match => `
            <div id="${match.Symbol}" class="card card-body mb-1" onClick="reply_click(this.id)">
            <h4 >${match.Name}(${match.Symbol})</h4>
            </div>
            `)
            .join('');

        matchList.innerHTML = html;
        }
    }

const reply_click = (clicked_id) => {
    console.log("Value", clicked_id);
    const clickedTicker = clicked_id;
    return clickedTicker
}

search.addEventListener('input', () => searchStates(search.value));
