const puppeteer = require('puppeteer');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const fs = require('fs');
const program = require('commander');
const CONFIG = require('./config.json');

const login_reddit = async (page) => {
    let cookies;
    if (fs.existsSync(CONFIG.COOKIE_PATH)) {
        const json = JSON.parse(fs.readFileSync(CONFIG.COOKIE_PATH, 'utf8'));
        cookies = json.cookies;
    } else {
        await page.goto('https://www.reddit.com/login/', {timeout: 60000, waitUntil: 'domcontentloaded'});
        await page.waitForSelector('#loginUsername');
        await page.type('#loginUsername', CONFIG.username);
        await page.type('#loginPassword', CONFIG.password);

        await page.click('[type="submit"]');
        await page.waitForNavigation({timeout: 60000, waitUntil: 'networkidle0'});

        cookies = await page.cookies();
        const json = JSON.stringify({cookies});
        fs.writeFileSync(CONFIG.COOKIE_PATH, json, 'utf8');
    }

    return cookies;
}

const mkdirIfNotExists = (path) => {
    if(!fs.existsSync(path)) {
        fs.mkdirSync(path);
    }
}
var removeDirContents = function(path) {
    if (fs.existsSync(path)) {
        fs.readdirSync(path).forEach((file) => {
            const curPath = `${path}/${file}`;
            if (fs.lstatSync(curPath).isFile()) {
                fs.unlinkSync(curPath);
            }
        });
    }
};

const replace_phrases = {
    'AMA': 'Ask Me Anything',
    'TIFU': 'Today I Effed up'
}
const reddit_replace = (string) => {
    let newString = string.trim()
    for (let [key, value] of Object.entries(replace_phrases)) {
        newString = newString.replace(new RegExp(key, "ig"), value);
    }
    return newString;
}

const sentence_regex = /([^,\.!\?;]+[,\.!\?;]+)|([^,\.!\?;]+$)/g;
const split_paragraphs = (paras) => {
    let flattened_sentences = [];
    const para_sentences = paras.map((para) => {
        const split = para.match(sentence_regex);
        if (!split) return [];

        let prev = "";
        const sentences = split.map((sentence) => {
            prev += sentence;
            return prev;
        });

        flattened_sentences = flattened_sentences.concat(split);

        return sentences;
    });

    return [flattened_sentences, para_sentences];
}
const addslashes = (str) => (str + '').replace(/[\\"']/g, '\\$&').replace(/\u0000/g, '\\0');

const url_regex = /(?:https?|ftp):\/\/[\n\S]+/g;
const clean_text = (str) => {
    if (!str) return '';
    const og_len = str.length
    let new_text = str.replace(url_regex, '');

    // if we remove most of the text it's probably useless (e.g. Proof: https://www.bla.com)
    if (og_len > (new_text.length * 5)) return '';
    return new_text;
};

const exposed_funcs = [split_paragraphs, clean_text];

const fetchAndSave = async (subReddit, postId) => {

    // Directory creation
    mkdirIfNotExists('text');
    mkdirIfNotExists('img');

    const rootImgPath = `img/${subReddit}_${postId}`;
    removeDirContents(rootImgPath);
    mkdirIfNotExists(rootImgPath);

    // Fetch the screenshot from the specified subreddit page
    const browser = await puppeteer.launch({headless: true});

    const context = browser.defaultBrowserContext();
    await context.overridePermissions('https://www.reddit.com', ['notifications']);

    const page = (await browser.pages())[0];
    page.setDefaultTimeout(60000);
    page.on('console', consoleObj => console.log(consoleObj.text()));

    await page.setViewport({ width: 800, height: 600, deviceScaleFactor: 2 })

    // Functions need to be explicitely expose to be acessed within the node context
    exposed_funcs.forEach(async (func) => {
        await page.exposeFunction(func.name, func);
    });

    const cookies = await login_reddit(page);
    await page.setCookie(...cookies);

    const topDivs = `div.SubredditVars-r-${subReddit}`;

    const url = `https://www.reddit.com/r/${subReddit}/comments/${postId}/?sort=top`;
    console.log(`Going to ${url} ...`)
    await page.goto(url, {waitUntil: 'domcontentloaded'});
    await page.waitForSelector(`${topDivs}:nth-of-type(2) div`);
    await page.waitFor(500); // Timeout hack to get shit to work (why do I need this?)

    // Up vote page :)
    if (await page.$('[data-click-id="upvote"][aria-pressed="false"][id^="upvote-button-"]') !== null) {
        await page.click('[data-click-id="upvote"][aria-pressed="false"][id^="upvote-button-"]');
    }

    // Delete stuff from the page that is unnecessary
    await page.evaluate((topDivs) => {
        // Remove margin
        let dom = document.querySelector(`${topDivs}:nth-of-type(2) div`);
        dom.style['margin-top'] = '0px';

        let nodes = document.querySelectorAll('div[data-test-id="post-content"] > div');

        if (nodes.length == 6) { // post with tags
            nodes[nodes.length-2].style['display'] = 'none';
        }
        nodes[nodes.length-1].style['display'] = 'none';

        // Delete header
        dom = document.querySelector(topDivs);
        dom.parentNode.removeChild(dom);

        nodes = document.querySelectorAll(`${topDivs} > div`);
        nodes.forEach(node => {
            node.style['margin-top'] = '0px';
        });
    }, topDivs);

    console.log(`Waiting for comments to load...`)
    await page.waitFor(10000); // Timeout hack --> comments are loaded below-the-fold so just wait a while for a bunch to load

    // Take screenshot of just the title and upvote buttons
    const titleDiv = await page.evaluateHandle(() => document.querySelector('div[data-test-id="post-content"]').parentElement);
    await titleDiv.screenshot({path: `${rootImgPath}/title.jpeg`, quality: 100});

    // Re-display the post-content text and comment numbers
    await page.evaluate(() => {
        let nodes = document.querySelectorAll('div[data-test-id="post-content"] > div');
        nodes[nodes.length-2].style['display'] = 'block';
    });

    const nodes = await page.$$('div[data-test-id="post-content"] > div');
    const title = await page.evaluate(div => div.querySelector('div').textContent.trim(), nodes[2]);
    let pars = null
    const rows = [{name: 'title', type: 'title', path: `${rootImgPath}/title.jpeg`, text: reddit_replace(title), group: 0}];

    // Start comment scraping
    const comments = await page.$$('div.Comment');
    const maxOverallComments = Math.min(comments.length, 10);
    const maxTopLevelComments = Math.min(comments.length, 3);
    const maxSubComments = 3; // includes top level comment
    let topBoundBox = null;

    let comment_index = 0;
    let top_level_comment_index = -1;
    let sub_comment_index = 0;
    
    console.log(`Found ${comments.length} comments. Processing...`);
    for (var i=0; i<comments.length && comment_index < maxOverallComments && top_level_comment_index < maxTopLevelComments; ++i) {
        const commentHeader = await comments[i].$('div:nth-of-type(2) > div:nth-of-type(1) > span:last-of-type');
        const svgIcon = await comments[i].$('div:nth-of-type(2) > div:nth-of-type(1) > svg');
        const stickedText = await (await commentHeader.getProperty('textContent')).jsonValue();
        const svgIconType = svgIcon && await (await svgIcon.getProperty('id')).jsonValue();

        if (svgIconType && svgIconType.includes('Mod')) continue; // ignore mod comments
        if (stickedText == 'Stickied comment') continue; // ignore stickied comments

        pars = await page.evaluateHandle(div => div.querySelectorAll('div:nth-of-type(2) > div[data-test-id="comment"] > div > p, ul > li'), comments[i]);
        const [split_sentences, para_sentences] = await page.evaluate(async (pars) => {
            const text = [];
            for (const p of pars) {
                const cleanedText = await clean_text(p.textContent);
                if (cleanedText) {
                    text.push(cleanedText);
                }
                p.style['display'] = 'none';
            }
            return split_paragraphs(text);
        }, pars);

        if (para_sentences.length == 0) continue; // ignore non-comments (expand buttons)

        const commentDescriptionSpan = await page.evaluateHandle(div => div.querySelector('div:nth-of-type(2) > span'), comments[i]);
        const level = await page.evaluate(x => x.textContent, commentDescriptionSpan)
        const classNamePromise = await comments[i].getProperty('className');
        const className = await classNamePromise.jsonValue();
        const isTopLevelComment = level === 'level 1' || className.includes('top-level');

        sub_comment_index = isTopLevelComment ? 0 : sub_comment_index + 1;
        if (isTopLevelComment) {
            ++top_level_comment_index;
        }
        if (top_level_comment_index >= maxTopLevelComments) continue;
        if (sub_comment_index >= maxSubComments) continue;

        let sentence_index = 0;
        for (var j=0; j<para_sentences.length; ++j) {
            // Un-hide individual paragraphs
            await page.evaluate((pars, j) => {
                pars[j].style['display'] = pars[j].nodeName == 'LI' ? 'list-item' : 'block';
            }, pars, j);

            for (const para_sentence of para_sentences[j]) {
                const name = `comment${top_level_comment_index}_level${sub_comment_index}_frame${sentence_index}`;
                const path = `${rootImgPath}/${name}.jpeg`;
                const text = reddit_replace(split_sentences[sentence_index]);

                // Change the text of the current paragraph to add in the next sentence
                await page.evaluate((pars, j, para_sentence) => { pars[j].innerHTML = para_sentence }, pars, j, para_sentence);

                let boundingBox = await comments[i].boundingBox();
                if (!isTopLevelComment) {
                    boundingBox.x = topBoundBox.x;
                    boundingBox.y = topBoundBox.y;
                    boundingBox.width = topBoundBox.width;
                    boundingBox.height += topBoundBox.height;
                }

                await page.screenshot({path, quality: 100, clip: boundingBox});

                rows.push({name, type: 'comment', path, text, group: top_level_comment_index + 2});
                ++sentence_index;
            }
        }

        let tmpTopBoundBox = await comments[i].boundingBox();
        if (isTopLevelComment) {
            topBoundBox = tmpTopBoundBox
        } else {
            topBoundBox.height += tmpTopBoundBox.height;
        }

        ++comment_index;
    }

    console.log(`Successfully got ${rows.length-1} comments. ${top_level_comment_index+1} top level comments`)

    // Start post scraping (needs to be after comments otherwise there is some clipping issue)
    pars = await page.evaluateHandle(div => div.querySelectorAll('div > p, ul > li'), nodes[4]);

    // Hide paragraphs, get text
    const [split_sentences, para_sentences] = await page.evaluate(async (pars) => {
        const text = [];
        for (const p of pars) {
            const cleanedText = await clean_text(p.textContent)
            if (cleanedText) {
                text.push(p.textContent);
            }
            p.style['display'] = 'none';
        }
        return split_paragraphs(text);
    }, pars);

    let sentence_index = 0;
    for (var i=0; i<para_sentences.length; ++i) {
        // Un-hide individual paragraphs
        await page.evaluate((pars, i) => {
            pars[i].style['display'] = pars[i].nodeName == 'LI' ? 'list-item' : 'block';
        }, pars, i);

        for (const para_sentence of para_sentences[i]) {
            const name = `post_frame${sentence_index}`;
            const path = `${rootImgPath}/${name}.jpeg`;
            const text = reddit_replace(split_sentences[sentence_index]);
            // Change the text of the current paragraph to add in the next sentence
            await page.evaluate((pars, i, para_sentence) => { pars[i].innerHTML = para_sentence }, pars, i, para_sentence);
            await titleDiv.screenshot({path, quality: 100});

            rows.push({name, type: 'post', path, text, group: 1});
            ++sentence_index;
        }
    }

    const csvWriter = createCsvWriter({  
        path: `text/${subReddit}_${postId}.csv`,
        header: [{id: 'name', title: 'Name'}, {id: 'type', title: 'Type'}, {id: 'path', title: 'Path'}, {id: 'text', title: 'Text'}, {id: 'group', title: 'Group'}]
    });

    await csvWriter.writeRecords(rows);

    await browser.close();
};

program
  .version('0.0.1', '-v, --version')
  .arguments('<subreddit> <postid>')
  .on('--help', function(){
    console.log('')
    console.log('Examples:');
    console.log(`  $ node ${process.argv[1]} uwaterloo 9uhk57`);
  })
  .action(fetchAndSave)
  .parse(process.argv);

module.exports.fetchAndSave = fetchAndSave;
